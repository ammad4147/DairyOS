const { app, BrowserWindow, dialog } = require('electron');
const { spawn, spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const APP_PORT = 8000;
const PG_PORT = 55432;
const APP_NAME = 'DairyOS';
const DATA_ROOT = path.join(process.env.ProgramData || path.join(process.env.SystemDrive || 'C:', 'ProgramData'), APP_NAME);
const DB_ROOT = path.join(DATA_ROOT, 'postgresql-data');
const BACKUP_ROOT = path.join(DATA_ROOT, 'backups');
const RECOVERY_ROOT = path.join(DATA_ROOT, 'recovery');
const CONFIG_PATH = path.join(DATA_ROOT, 'desktop-config.json');

let postgresProcess = null;
let backendProcess = null;
let mainWindow = null;
let shuttingDown = false;

function resourcePath(...parts) {
  return path.join(process.resourcesPath, ...parts);
}

function binaryPath(relative) {
  const packaged = resourcePath(relative);
  if (fs.existsSync(packaged)) return packaged;
  return path.join(__dirname, relative);
}

function ensureDirectories() {
  for (const directory of [DATA_ROOT, DB_ROOT, BACKUP_ROOT, RECOVERY_ROOT]) {
    fs.mkdirSync(directory, { recursive: true });
  }
}

function loadConfig() {
  ensureDirectories();
  if (fs.existsSync(CONFIG_PATH)) {
    return JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));
  }

  const config = {
    database_user: 'dairyos',
    database_name: 'dairyos',
    database_password: crypto.randomBytes(32).toString('base64url'),
    database_port: PG_PORT,
    data_root: DATA_ROOT,
    created_at: new Date().toISOString(),
  };

  fs.writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2), { encoding: 'utf8', mode: 0o600 });
  return config;
}

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    windowsHide: true,
    encoding: 'utf8',
    stdio: options.capture === false ? 'ignore' : ['ignore', 'pipe', 'pipe'],
    env: options.env || process.env,
  });

  if (result.error) throw result.error;
  if (result.status !== 0) {
    const message = `${command} failed with exit code ${result.status}.\n${result.stderr || ''}`.trim();
    throw new Error(message);
  }
  return result.stdout || '';
}

function isPostgresInitialized() {
  return fs.existsSync(path.join(DB_ROOT, 'PG_VERSION'));
}

function isPostgresRunning(pgctl) {
  const result = spawnSync(pgctl, ['status', '-D', DB_ROOT], {
    windowsHide: true,
    encoding: 'utf8',
    stdio: 'ignore',
  });
  return result.status === 0;
}

function initializePostgres(config, initdb) {
  if (isPostgresInitialized()) return;
  const passwordFile = path.join(DATA_ROOT, '.postgres-password');
  fs.writeFileSync(passwordFile, `${config.database_password}\n`, { encoding: 'utf8', mode: 0o600 });

  run(initdb, [
    '-D', DB_ROOT,
    '-U', config.database_user,
    '-A', 'scram-sha-256',
    '--pwfile=' + passwordFile,
    '--encoding=UTF8',
  ]);

  fs.rmSync(passwordFile, { force: true });
}

function startPostgres(config) {
  const pgctl = binaryPath(path.join('postgresql', 'bin', 'pg_ctl.exe'));
  const initdb = binaryPath(path.join('postgresql', 'bin', 'initdb.exe'));
  const psql = binaryPath(path.join('postgresql', 'bin', 'psql.exe'));

  if (!fs.existsSync(pgctl) || !fs.existsSync(initdb) || !fs.existsSync(psql)) {
    throw new Error('DairyOS PostgreSQL runtime is missing from the installation.');
  }

  initializePostgres(config, initdb);

  if (!isPostgresRunning(pgctl)) {
    const logFile = path.join(DATA_ROOT, 'postgresql.log');
    run(pgctl, [
      'start', '-D', DB_ROOT, '-l', logFile, '-w', '-t', '30',
      '-o', `-p ${PG_PORT} -h 127.0.0.1`,
    ]);
  }

  const env = { ...process.env, PGPASSWORD: config.database_password };
  const ready = spawnSync(psql, [
    '-h', '127.0.0.1', '-p', String(PG_PORT),
    '-U', config.database_user, '-d', config.database_name,
    '-c', 'SELECT 1;',
  ], { windowsHide: true, encoding: 'utf8', stdio: 'ignore', env });

  if (ready.status !== 0) {
    throw new Error('DairyOS PostgreSQL started but the application database is not accepting connections.');
  }
}

function backupDatabase(config, reason) {
  const pgDump = binaryPath(path.join('postgresql', 'bin', 'pg_dump.exe'));
  if (!fs.existsSync(pgDump)) throw new Error('pg_dump.exe is missing from the DairyOS installation.');

  fs.mkdirSync(BACKUP_ROOT, { recursive: true });
  const stamp = new Date().toISOString().replace(/[:.]/g, '-');
  const target = path.join(BACKUP_ROOT, `${stamp}-${reason}.dump`);
  const env = { ...process.env, PGPASSWORD: config.database_password };

  run(pgDump, [
    '-h', '127.0.0.1', '-p', String(PG_PORT),
    '-U', config.database_user, '-d', config.database_name,
    '-F', 'c', '--no-owner', '--no-acl', '-f', target,
  ], { env });

  const files = fs.readdirSync(BACKUP_ROOT)
    .filter(name => name.toLowerCase().endsWith('.dump'))
    .map(name => ({ name, time: fs.statSync(path.join(BACKUP_ROOT, name)).mtimeMs }))
    .sort((a, b) => b.time - a.time);

  for (const file of files.slice(30)) {
    fs.rmSync(path.join(BACKUP_ROOT, file.name), { force: true });
  }

  return target;
}

function startBackend(config) {
  const server = binaryPath(path.join('backend', 'dairyos-server.exe'));
  if (!fs.existsSync(server)) throw new Error('DairyOS backend runtime is missing from the installation.');

  const databaseUrl = `postgresql+psycopg://${encodeURIComponent(config.database_user)}:${encodeURIComponent(config.database_password)}@127.0.0.1:${PG_PORT}/${encodeURIComponent(config.database_name)}`;
  const env = {
    ...process.env,
    DAIRYOS_ENV: 'production',
    DAIRYOS_HOST: '127.0.0.1',
    DAIRYOS_PORT: String(APP_PORT),
    DAIRYOS_DATA_DIR: DATA_ROOT,
    DAIRYOS_DATABASE_URL: databaseUrl,
  };

  backendProcess = spawn(server, ['--host', '127.0.0.1', '--port', String(APP_PORT), '--data-dir', DATA_ROOT], {
    windowsHide: true,
    env,
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  backendProcess.stdout.on('data', chunk => fs.appendFileSync(path.join(DATA_ROOT, 'backend.log'), chunk));
  backendProcess.stderr.on('data', chunk => fs.appendFileSync(path.join(DATA_ROOT, 'backend-error.log'), chunk));
  backendProcess.on('exit', code => {
    if (!shuttingDown && code !== 0) {
      dialog.showErrorBox('DairyOS stopped', `The DairyOS backend stopped unexpectedly (exit code ${code}).\n\nYour farm data remains in:\n${DATA_ROOT}`);
      if (mainWindow) mainWindow.close();
    }
  });
}

async function waitForHealth() {
  const deadline = Date.now() + 30000;
  let lastError = 'not started';
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`http://127.0.0.1:${APP_PORT}/health`, { method: 'GET' });
      if (response.ok) {
        const body = await response.json();
        if (body?.status === 'healthy') return;
        lastError = JSON.stringify(body);
      } else {
        lastError = `HTTP ${response.status}`;
      }
    } catch (error) {
      lastError = String(error);
    }
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  throw new Error(`DairyOS did not become healthy within 30 seconds. Last check: ${lastError}`);
}

async function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
    backgroundColor: '#0b0f19',
    autoHideMenuBar: true,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  await mainWindow.loadFile(resourcePath('frontend', 'index.html'));
  mainWindow.on('closed', () => { mainWindow = null; });
}

function stopProcessTree(child) {
  if (!child || child.killed) return;
  try {
    spawnSync('taskkill', ['/PID', String(child.pid), '/T', '/F'], { windowsHide: true, stdio: 'ignore' });
  } catch (_) {
    // Best-effort shutdown; data is stored independently of the application process.
  }
}

function stopPostgres() {
  const pgctl = binaryPath(path.join('postgresql', 'bin', 'pg_ctl.exe'));
  if (fs.existsSync(pgctl) && isPostgresRunning(pgctl)) {
    spawnSync(pgctl, ['stop', '-D', DB_ROOT, '-m', 'fast', '-w'], { windowsHide: true, stdio: 'ignore' });
  }
}

async function shutdown() {
  if (shuttingDown) return;
  shuttingDown = true;
  stopProcessTree(backendProcess);
  stopPostgres();
  backendProcess = null;
  postgresProcess = null;
}

async function boot() {
  ensureDirectories();
  const config = loadConfig();

  startPostgres(config);
  if (isPostgresInitialized()) {
    // Existing databases are backed up before the application server is
    // started, because application startup may perform schema migrations.
    // A failed backup is fail-safe: the application does not start.
    backupDatabase(config, 'prestart');
  }

  startBackend(config);
  await waitForHealth();
  await createWindow();
}

app.whenReady().then(async () => {
  try {
    await boot();
  } catch (error) {
    await shutdown();
    dialog.showErrorBox(
      'DairyOS could not start safely',
      `${error instanceof Error ? error.message : String(error)}\n\nFarm data has not been removed.\n\nData location:\n${DATA_ROOT}\n\nBackups:\n${BACKUP_ROOT}`,
    );
    app.quit();
  }
});

app.on('before-quit', event => {
  if (!shuttingDown) {
    event.preventDefault();
    void shutdown().finally(() => app.quit());
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { webcrypto } = require('node:crypto');
const { TextEncoder } = require('node:util');
const ts = require('../../src/DairyOS.Web/node_modules/typescript');

const source = fs.readFileSync(
  path.resolve(__dirname, '../../src/DairyOS.Web/src/api/farmEntryClient.ts'),
  'utf8',
);
const javascript = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText;

function createClient(fetchImpl) {
  const saved = new Map();
  const storage = {
    get length() { return saved.size; },
    getItem: key => saved.get(key) ?? null,
    setItem: (key, value) => saved.set(key, String(value)),
    removeItem: key => saved.delete(key),
    key: index => [...saved.keys()][index] ?? null,
  };
  const module = { exports: {} };
  vm.runInNewContext(javascript, {
    exports: module.exports,
    require: name => {
      assert.equal(name, '../config/api');
      return { apiUrl: value => value };
    },
    crypto: webcrypto,
    fetch: fetchImpl,
    sessionStorage: storage,
    TextEncoder,
    Date,
    Map,
    JSON,
    Uint8Array,
  });
  return { api: module.exports, storage };
}

function response(status, body = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json' },
  });
}

async function run() {
  const calls = [];
  let nextFetch = async (_url, init) => {
    calls.push(JSON.parse(init.body));
    throw new Error('simulated lost response');
  };
  const client = createClient((...args) => nextFetch(...args));
  const payload = { animal_id: 'TEST-1', observation: 'test', operator: 'test' };

  await assert.rejects(client.api.postRequest('/farm/health-observations', payload));
  const retryMarkerKey = [...Array(client.storage.length).keys()]
    .map(index => client.storage.key(index))
    .find(name => name?.startsWith('dairyos:uncertain-write:'));
  assert.ok(retryMarkerKey, 'network ambiguity must persist an expiring retry marker');
  const firstId = JSON.parse(client.storage.getItem(retryMarkerKey)).requestId;

  nextFetch = async (_url, init) => {
    calls.push(JSON.parse(init.body));
    return response(500, { detail: 'temporary server error' });
  };
  await assert.rejects(client.api.postRequest('/farm/health-observations', payload));
  assert.equal(calls.at(-1).request_id, firstId, '5xx retries must reuse the uncertain request ID');

  nextFetch = async (_url, init) => {
    calls.push(JSON.parse(init.body));
    return response(200, { saved: true });
  };
  await client.api.postRequest('/farm/health-observations', payload);
  assert.equal(calls.at(-1).request_id, firstId);
  assert.equal(client.storage.length, 0, 'confirmed success clears the retry marker');

  const expiryClient = createClient(async () => { throw new Error('simulated lost response'); });
  await assert.rejects(expiryClient.api.postRequest('/farm/feed', { feed_type: 'test', quantity_kg: 1 }));
  const expiryKey = [...Array(expiryClient.storage.length).keys()]
    .map(index => expiryClient.storage.key(index))
    .find(name => name?.startsWith('dairyos:uncertain-write:'));
  const expiredId = JSON.parse(expiryClient.storage.getItem(expiryKey)).requestId;
  let freshId;
  const expiredRetryClient = createClient(async (_url, init) => {
    freshId = JSON.parse(init.body).request_id;
    return response(200, { saved: true });
  });
  expiredRetryClient.storage.setItem(
    expiryKey,
    JSON.stringify({ requestId: expiredId, expiresAt: Date.now() - 1 }),
  );
  await expiredRetryClient.api.postRequest('/farm/feed', { feed_type: 'test', quantity_kg: 1 });
  assert.notEqual(freshId, expiredId, 'expired markers must not swallow a new identical entry');

  const logoutClient = createClient(async () => { throw new Error('simulated lost response'); });
  await assert.rejects(logoutClient.api.postRequest('/farm/feed', { feed_type: 'test', quantity_kg: 2 }));
  assert.ok(logoutClient.storage.length > 0);
  logoutClient.api.clearUncertainWriteMarkers();
  assert.equal(logoutClient.storage.length, 0, 'logout cleanup clears persisted uncertain markers');

  console.log('PASS: uncertain-write retry identity, 5xx retention, expiry, success cleanup, logout cleanup');
}

run().catch(error => {
  console.error(error);
  process.exitCode = 1;
});

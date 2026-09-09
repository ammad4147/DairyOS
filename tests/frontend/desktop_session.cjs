const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('../../src/DairyOS.Web/node_modules/typescript');
const source = fs.readFileSync(path.resolve(__dirname, '../../src/DairyOS.Web/src/config/desktopSession.ts'), 'utf8');
const javascript = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText;
const saved = new Map();
const calls = [];
const window = {
  location: { hash: '#desktop-session=private-test-token', href: 'http://127.0.0.1:58000/', origin: 'http://127.0.0.1:58000', pathname: '/', search: '' },
  sessionStorage: { setItem: (k, v) => saved.set(k, v), getItem: k => saved.get(k) },
  history: { replaceState: (_state, _unused, url) => { assert.equal(url, '/'); window.location.hash = ''; } },
  fetch: (input, init) => { calls.push({ input, init }); return Promise.resolve({ ok: true }); },
};
const context = { exports: {}, window, URL, URLSearchParams, Headers, Request };
vm.runInNewContext(javascript, context);
context.exports.installDesktopSession();
assert.equal(window.location.hash, '');
window.fetch('/farm/feed-inventory/items');
assert.equal(calls.at(-1).init.headers.get('X-DairyOS-Desktop-Session'), 'private-test-token');
window.fetch('http://127.0.0.1:59000/other-service');
assert.equal(calls.at(-1).init, undefined);
window.fetch('https://example.invalid/external');
assert.equal(calls.at(-1).init, undefined);
window.fetch(new Request('http://127.0.0.1:58000/farm/inventory', { headers: { 'X-Existing': 'preserved' } }));
assert.equal(calls.at(-1).init.headers.get('X-Existing'), 'preserved');
assert.equal(calls.at(-1).init.headers.get('X-DairyOS-Desktop-Session'), 'private-test-token');
assert.equal(new URL(context.exports.desktopWindowUrl('/?window=payroll')).hash, '#desktop-session=private-test-token');
assert.equal(new URL(context.exports.desktopWindowUrl('https://example.invalid')).hash, '');
console.log('PASS: session initialization, URL cleanup, same-origin request scope, header preservation, Payroll propagation, external-origin exclusion');

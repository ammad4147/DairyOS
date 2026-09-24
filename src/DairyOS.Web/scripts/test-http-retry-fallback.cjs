const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const ts = require("typescript");

const sourcePath = path.join(__dirname, "..", "src", "api", "farmEntryClient.ts");
const source = fs.readFileSync(sourcePath, "utf8");
const compiled = ts.transpileModule(source, {
    compilerOptions: {
        module: ts.ModuleKind.CommonJS,
        target: ts.ScriptTarget.ES2020,
    },
}).outputText;

const storage = new Map();
const sentRequestIds = [];
let entropyByte = 0;
let requestCount = 0;
const testModule = { exports: {} };
const context = {
    module: testModule,
    exports: testModule.exports,
    require: () => ({ apiUrl: (url) => url }),
    TextEncoder,
    Uint8Array,
    Math,
    Date,
    JSON,
    Array,
    Map,
    Promise,
    Error,
    sessionStorage: {
        getItem: (key) => storage.get(key) ?? null,
        setItem: (key, value) => storage.set(key, value),
        removeItem: (key) => storage.delete(key),
        get length() { return storage.size; },
        key: (index) => [...storage.keys()][index] ?? null,
    },
    // Private-LAN HTTP has no SubtleCrypto or randomUUID in this test context.
    crypto: {
        subtle: undefined,
        randomUUID: undefined,
        getRandomValues: (bytes) => {
            for (let index = 0; index < bytes.length; index += 1) {
                bytes[index] = (++entropyByte) & 0xff;
            }
            return bytes;
        },
    },
    fetch: async (_url, options) => {
        sentRequestIds.push(JSON.parse(options.body).request_id);
        requestCount += 1;
        if (requestCount === 1) throw new Error("simulated lost response");
        return { ok: true, status: 200, json: async () => ({ accepted: true }) };
    },
};
context.globalThis = context;
vm.runInNewContext(compiled, context);

const milkEntry = {
    animal_id: "test-only-animal",
    morning_yield: 1,
    afternoon_yield: 0,
    evening_yield: 0,
    operator: "test-only",
};

(async () => {
    await assert.rejects(testModule.exports.postRequest("/farm/milk", milkEntry));
    const differentEntry = { ...milkEntry, morning_yield: 2 };
    await testModule.exports.postRequest("/farm/milk", differentEntry);
    await testModule.exports.postRequest("/farm/milk", milkEntry);

    assert.equal(sentRequestIds.length, 3);
    assert.equal(sentRequestIds[0], sentRequestIds[2], "identical retry must reuse its original request ID");
    assert.notEqual(sentRequestIds[0], sentRequestIds[1], "different payload must receive a different request ID");
    console.log("PASS: HTTP-origin writes work without SubtleCrypto/randomUUID; retries keep their ID and distinct entries do not reuse it.");
})().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});

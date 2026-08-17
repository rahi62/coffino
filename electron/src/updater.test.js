const assert=require("assert");
const {normalizeUpdateUrl,normalizeUpdateChannel}=require("./updater");

assert.strictEqual(normalizeUpdateUrl("http://updates.example.com/cafino"),"");
assert.strictEqual(normalizeUpdateUrl("not-a-url"),"");
assert.strictEqual(normalizeUpdateUrl("https://updates.example.com/cafino/"),"https://updates.example.com/cafino");
assert.strictEqual(normalizeUpdateChannel("stable"),"latest");
assert.strictEqual(normalizeUpdateChannel("latest"),"latest");
assert.strictEqual(normalizeUpdateChannel("beta"),"beta");
assert.strictEqual(normalizeUpdateChannel("nightly"),"");
console.log("updater tests passed");

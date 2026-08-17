const assert=require("assert");
const {normalizeUpdateUrl,normalizeUpdateChannel,inferUpdateChannel}=require("./updater");

assert.strictEqual(normalizeUpdateUrl("http://updates.example.com/cafino"),"");
assert.strictEqual(normalizeUpdateUrl("not-a-url"),"");
assert.strictEqual(normalizeUpdateUrl("https://updates.example.com/cafino/"),"https://updates.example.com/cafino");
assert.strictEqual(normalizeUpdateChannel("stable"),"latest");
assert.strictEqual(normalizeUpdateChannel("latest"),"latest");
assert.strictEqual(normalizeUpdateChannel("beta"),"beta");
assert.strictEqual(normalizeUpdateChannel("nightly"),"");
assert.strictEqual(inferUpdateChannel("https://updates.example.com/cafino/local/stable"),"latest");
assert.strictEqual(inferUpdateChannel("https://updates.example.com/cafino/local/beta"),"beta");
assert.strictEqual(inferUpdateChannel("https://updates.example.com/cafino/local/stable","beta"),"beta");
console.log("updater tests passed");

const assert=require("assert");
const {normalizeUpdateUrl}=require("./updater");

assert.strictEqual(normalizeUpdateUrl("http://updates.example.com/cafino"),"");
assert.strictEqual(normalizeUpdateUrl("not-a-url"),"");
assert.strictEqual(normalizeUpdateUrl("https://updates.example.com/cafino/"),"https://updates.example.com/cafino");
console.log("updater tests passed");

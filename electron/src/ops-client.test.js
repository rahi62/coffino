const assert=require("assert");
const fs=require("fs");
const os=require("os");
const path=require("path");
const ops=require("./ops-client");

assert.strictEqual(ops.normalizeEndpoint("https://ops.example.com/api/ops/v1/"),"https://ops.example.com/api/ops/v1");
assert.strictEqual(ops.normalizeEndpoint("http://ops.example.com"),"");
assert.strictEqual(ops.normalizeEndpoint("not-a-url"),"");

const root=fs.mkdtempSync(path.join(os.tmpdir(),"cafino-ops-client-"));
try{
  const first=ops.loadState(root);const second=ops.loadState(root);
  assert.ok(first.installation_id);
  assert.strictEqual(first.installation_id,second.installation_id);
  first.device_token="secret-device-token";ops.saveState(root,first);
  assert.strictEqual(ops.loadState(root).device_token,"secret-device-token");
  ops.clearToken(root);assert.strictEqual(ops.loadState(root).device_token,"");

  const error=new Error("Customer phone 09120000000 must never be transmitted");
  error.stack="Error: private message\n    at C:\\Users\\PrivateUser\\cafino\\src\\x.js:1:2";
  const fingerprint=ops.fingerprintError(error,"electron");
  assert.match(fingerprint,/^[0-9a-f]{64}$/);
  assert.ok(!fingerprint.includes("0912"));
  assert.strictEqual(fingerprint,ops.fingerprintError(error,"electron"));
  console.log("ops-client tests passed");
}finally{fs.rmSync(root,{recursive:true,force:true});}

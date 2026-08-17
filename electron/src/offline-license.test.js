const assert=require("assert");
const crypto=require("crypto");
const license=require("./offline-license");

const {publicKey,privateKey}=crypto.generateKeyPairSync("ed25519");
const publicPem=publicKey.export({type:"spki",format:"pem"});
const machine=license.machineHash("WINDOWS-MACHINE-GUID-123");
const payload={product:"cafino-local",license_id:"LIC-001",customer:"Demo Cafe",machine_hash:machine,issued_at:"2026-08-17T00:00:00Z",expires_at:"2027-08-17T00:00:00Z",features:["POS","INVENTORY"]};
const signature=crypto.sign(null,Buffer.from(license.canonicalize(payload),"utf8"),privateKey).toString("base64");
const doc={payload,signature};

assert.strictEqual(license.verifyLicenseDocument(doc,publicPem,machine,{now:new Date("2026-09-01T00:00:00Z")}).ok,true);
assert.strictEqual(license.verifyLicenseDocument(doc,publicPem,license.machineHash("other"),{now:new Date("2026-09-01T00:00:00Z")}).reason,"machine_mismatch");
assert.strictEqual(license.verifyLicenseDocument(doc,publicPem,machine,{now:new Date("2028-01-01T00:00:00Z")}).reason,"expired");
const tampered=JSON.parse(JSON.stringify(doc));tampered.payload.customer="Tampered";
assert.strictEqual(license.verifyLicenseDocument(tampered,publicPem,machine,{now:new Date("2026-09-01T00:00:00Z")}).reason,"signature_invalid");
assert.ok(license.requestCode({machine_hash:machine,version:"1.1.0"}).length>20);
console.log("offline-license tests passed");

const fs=require("fs");
const path=require("path");
const crypto=require("crypto");
const {canonicalize}=require("../electron/src/offline-license");

function arg(name,fallback=""){const i=process.argv.indexOf(name);return i>=0&&process.argv[i+1]?process.argv[i+1]:fallback;}
const request=arg("--request");
const customer=arg("--customer");
const licenseId=arg("--license-id",`LIC-${Date.now()}`);
const expiresAt=arg("--expires","");
const businessId=arg("--business-id","");
const branchId=arg("--branch-id","");
const features=arg("--features","POS,INVENTORY,REPORTING").split(",").map(x=>x.trim()).filter(Boolean);
const out=path.resolve(arg("--out",`cafino-license-${licenseId}.json`));
const privateKeyPath=process.env.CAF_INO_LICENSE_PRIVATE_KEY_PATH;
if(!request)throw new Error("--request <request-code> is required");
if(!customer)throw new Error("--customer <name> is required");
if(!privateKeyPath||!fs.existsSync(privateKeyPath))throw new Error("CAF_INO_LICENSE_PRIVATE_KEY_PATH must point to the offline Ed25519 private key");
let requestPayload;try{requestPayload=JSON.parse(Buffer.from(request,"base64url").toString("utf8"))}catch{throw new Error("Invalid request code")}
if(requestPayload.product!=="cafino-local"||!requestPayload.machine_hash)throw new Error("Request code is not for Cafino Local");
const payload={
  product:"cafino-local",
  license_id:licenseId,
  customer,
  machine_hash:requestPayload.machine_hash,
  issued_at:new Date().toISOString(),
  features,
};
if(businessId){if(!/^\d+$/.test(businessId))throw new Error("--business-id must be numeric");payload.business_id=Number(businessId);}
if(branchId){if(!/^\d+$/.test(branchId))throw new Error("--branch-id must be numeric");payload.branch_id=Number(branchId);}
if(expiresAt){if(Number.isNaN(Date.parse(expiresAt)))throw new Error("--expires must be an ISO date/time");payload.expires_at=new Date(expiresAt).toISOString();}
const privateKey=fs.readFileSync(privateKeyPath,"utf8");
const signature=crypto.sign(null,Buffer.from(canonicalize(payload),"utf8"),privateKey).toString("base64");
fs.writeFileSync(out,JSON.stringify({payload,signature},null,2),"utf8");
console.log(`License written: ${out}`);
console.log(`Machine: ${payload.machine_hash}`);
if(payload.business_id)console.log(`Business ID: ${payload.business_id}`);
if(payload.branch_id)console.log(`Branch ID: ${payload.branch_id}`);

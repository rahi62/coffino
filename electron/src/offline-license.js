const crypto=require("crypto");
const fs=require("fs");
const os=require("os");

function canonicalize(value){
  if(Array.isArray(value))return`[${value.map(canonicalize).join(",")}]`;
  if(value&&typeof value==="object")return`{${Object.keys(value).sort().map(k=>`${JSON.stringify(k)}:${canonicalize(value[k])}`).join(",")}}`;
  return JSON.stringify(value);
}
function machineHash(identity){return crypto.createHash("sha256").update(`cafino-local|${String(identity||"")}`).digest("hex");}
function fallbackMachineIdentity(){return`${os.hostname()}|${process.platform}|${process.arch}`;}
function requestCode({machine_hash,version="",product="cafino-local"}){return Buffer.from(JSON.stringify({product,machine_hash,version}),"utf8").toString("base64url");}
function verifyLicenseDocument(document,publicKeyPem,expectedMachineHash,{now=new Date()}={}){
  if(!document||typeof document!=="object"||!document.payload||!document.signature)return{ok:false,reason:"invalid_document"};
  if(!publicKeyPem)return{ok:false,reason:"missing_public_key"};
  const payload=document.payload;
  if(payload.product!=="cafino-local")return{ok:false,reason:"wrong_product"};
  if(!payload.license_id||!payload.machine_hash)return{ok:false,reason:"missing_fields"};
  if(expectedMachineHash&&payload.machine_hash!==expectedMachineHash)return{ok:false,reason:"machine_mismatch"};
  let signature;
  try{signature=Buffer.from(document.signature,"base64")}catch{return{ok:false,reason:"invalid_signature_encoding"}}
  try{
    const valid=crypto.verify(null,Buffer.from(canonicalize(payload),"utf8"),publicKeyPem,signature);
    if(!valid)return{ok:false,reason:"signature_invalid"};
  }catch(error){return{ok:false,reason:"signature_error",error:String(error.message||error)}}
  const current=now.getTime();
  if(payload.not_before&&Date.parse(payload.not_before)>current)return{ok:false,reason:"not_active"};
  if(payload.expires_at&&Date.parse(payload.expires_at)<current)return{ok:false,reason:"expired",expires_at:payload.expires_at};
  return{ok:true,reason:"valid",license_id:payload.license_id,customer:payload.customer||"",expires_at:payload.expires_at||null,features:Array.isArray(payload.features)?payload.features:[]};
}
function loadLicense(file){try{return JSON.parse(fs.readFileSync(file,"utf8"))}catch{return null}}
function saveLicense(file,document){fs.writeFileSync(file,JSON.stringify(document,null,2),"utf8");return file;}

module.exports={canonicalize,machineHash,fallbackMachineIdentity,requestCode,verifyLicenseDocument,loadLicense,saveLicense};

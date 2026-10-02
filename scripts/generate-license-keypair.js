const fs=require("fs");
const path=require("path");
const crypto=require("crypto");

const root=path.resolve(__dirname,"..");
const out=path.resolve(process.argv[2]||path.join(root,"release-secrets"));
fs.mkdirSync(out,{recursive:true});
const privatePath=path.join(out,"license-private-key.pem");
const publicPath=path.join(out,"license-public-key.pem");
if(fs.existsSync(privatePath)||fs.existsSync(publicPath))throw new Error(`Refusing to overwrite existing key material in ${out}`);
const {publicKey,privateKey}=crypto.generateKeyPairSync("ed25519");
fs.writeFileSync(privatePath,privateKey.export({type:"pkcs8",format:"pem"}),{encoding:"utf8",mode:0o600});
fs.writeFileSync(publicPath,publicKey.export({type:"spki",format:"pem"}),"utf8");
console.log(`Private key: ${privatePath}`);
console.log(`Public key:  ${publicPath}`);
console.log("Keep the private key offline. Only the public key is packaged with Cafino Local.");

const assert=require("assert");
const fs=require("fs");
const path=require("path");

const root=path.resolve(__dirname,"..");
const electron=path.join(root,"electron");
const required=[
  "electron/electron-builder.config.cjs",
  "electron/src/entry.js",
  "electron/src/release-runtime.js",
  "electron/src/release-ops.js",
  "electron/src/offline-license.js",
  "electron/src/updater.js",
  "scripts/generate-license-keypair.js",
  "scripts/issue-license.js",
  "scripts/build-release.ps1",
  ".github/workflows/release-local.yml",
  ".github/workflows/windows-release-smoke.yml",
];
for(const rel of required)assert.ok(fs.existsSync(path.join(root,rel)),`Missing ${rel}`);
const pkg=JSON.parse(fs.readFileSync(path.join(electron,"package.json"),"utf8"));
assert.strictEqual(pkg.main,"src/entry.js");
assert.ok(pkg.dependencies?.["electron-updater"],"electron-updater dependency is required");
assert.ok(pkg.scripts?.["test:release"],"test:release script is required");
const builder=fs.readFileSync(path.join(electron,"electron-builder.config.cjs"),"utf8");
for(const token of ["forceCodeSigning","nsis","artifactName","CAF_INO_UPDATE_URL","CAF_INO_UPDATE_CHANNEL","publishAutoUpdate","CAF_INO_UPDATE_URL must use HTTPS"])assert.ok(builder.includes(token),`Builder contract missing ${token}`);
const updater=fs.readFileSync(path.join(electron,"src","updater.js"),"utf8");
for(const token of ["normalizeUpdateChannel","inferUpdateChannel","beta","allowDowngrade=false"])assert.ok(updater.includes(token),`Updater channel contract missing ${token}`);
const build=fs.readFileSync(path.join(root,"scripts","build-release.ps1"),"utf8");
for(const token of ["CAF_INO_UPDATE_BASE_URL","CAF_INO_UPDATE_URL","CAF_INO_LICENSE_PUBLIC_KEY_PATH","CSC_LINK","CSC_KEY_PASSWORD","ValidateSet(\"stable\",\"beta\")","latest.yml","beta.yml","release-manifest.json","SHA256"])assert.ok(build.includes(token),`Production build gate missing ${token}`);
const workflow=fs.readFileSync(path.join(root,".github","workflows","release-local.yml"),"utf8");
for(const token of ["channel:","publish:","Verify Authenticode","publish-update-feed","CAF_INO_UPDATE_BUCKET","CAF_INO_UPDATE_ENDPOINT","no-cache,no-store,must-revalidate"])assert.ok(workflow.includes(token),`Production release workflow missing ${token}`);
const smoke=fs.readFileSync(path.join(root,".github","workflows","windows-release-smoke.yml"),"utf8");
for(const token of ["Silent install","Cafino.exe","api/v1/health","127.0.0.1:3000","Uninstall*.exe"])assert.ok(smoke.includes(token),`Windows installed smoke contract missing ${token}`);
console.log("Cafino desktop release contract passed");

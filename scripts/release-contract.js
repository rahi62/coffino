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
  "scripts/prepare-update-feed.ps1",
  "scripts/smoke-test-installer.ps1",
  ".github/workflows/release-local.yml",
];
for(const rel of required)assert.ok(fs.existsSync(path.join(root,rel)),`Missing ${rel}`);
const pkg=JSON.parse(fs.readFileSync(path.join(electron,"package.json"),"utf8"));
assert.strictEqual(pkg.main,"src/entry.js");
assert.ok(pkg.dependencies?.["electron-updater"],"electron-updater dependency is required");
assert.ok(pkg.scripts?.["test:release"],"test:release script is required");
const builder=fs.readFileSync(path.join(electron,"electron-builder.config.cjs"),"utf8");
for(const token of ["forceCodeSigning","nsis","artifactName","CAF_INO_UPDATE_URL","CAF_INO_UPDATE_URL must use HTTPS"])assert.ok(builder.includes(token),`Builder contract missing ${token}`);
const build=fs.readFileSync(path.join(root,"scripts","build-release.ps1"),"utf8");
for(const token of ["CAF_INO_UPDATE_URL","CAF_INO_LICENSE_PUBLIC_KEY_PATH","CSC_LINK","CSC_KEY_PASSWORD","release-manifest.json","SHA256","releaseChannel","prepare-update-feed.ps1"])assert.ok(build.includes(token),`Production build gate missing ${token}`);
const workflow=fs.readFileSync(path.join(root,".github","workflows","release-local.yml"),"utf8");
for(const token of ["stable","beta","CAF_INO_UPDATE_BASE_URL","smoke-test-installer.ps1","publish_update_feed","CAF_INO_UPDATE_BUCKET"])assert.ok(workflow.includes(token),`Production workflow missing ${token}`);
const entry=fs.readFileSync(path.join(electron,"src","entry.js"),"utf8");
assert.ok(entry.includes("--cafino-smoke-check"),"Packaged smoke-check entrypoint is required");
console.log("Cafino desktop release contract passed");

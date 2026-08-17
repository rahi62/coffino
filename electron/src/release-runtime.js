const {app,dialog,clipboard,ipcMain}=require("electron");
const {spawnSync}=require("child_process");
const fs=require("fs");
const path=require("path");
const crypto=require("crypto");
const {createUpdater}=require("./updater");
const license=require("./offline-license");
const ops=require("./release-ops");

let updater=null;
let updateState={enabled:false,status:"disabled"};
let scheduleTimer=null;
let releaseConfig=null;

function dataDir(){const d=app.getPath("userData");fs.mkdirSync(d,{recursive:true});return d;}
function dbPath(){return path.join(dataDir(),"cafino.sqlite3");}
function devBackendDir(){return path.resolve(__dirname,"../../backend");}
function devPython(){const d=devBackendDir();return process.platform==="win32"?path.join(d,".venv","Scripts","python.exe"):path.join(d,".venv","bin","python");}
function packagedBackend(){return path.join(process.resourcesPath,"backend",process.platform==="win32"?"cafino-backend.exe":"cafino-backend");}
function backendEnv(){
  const secretFile=path.join(dataDir(),"secret.key");
  if(!fs.existsSync(secretFile))fs.writeFileSync(secretFile,crypto.randomBytes(48).toString("hex"),{mode:0o600});
  return{...process.env,DATABASE_URL:`sqlite:///${dbPath().replace(/\\/g,"/")}`,DJANGO_SECRET_KEY:fs.readFileSync(secretFile,"utf8"),DJANGO_DEBUG:"0",DJANGO_ALLOWED_HOSTS:"127.0.0.1,localhost",DJANGO_SECURE_SSL_REDIRECT:"0",CAF_INO_ENV:"local"};
}
function devEnv(){const db=path.join(devBackendDir(),"db.sqlite3");return{...process.env,DATABASE_URL:`sqlite:///${db.replace(/\\/g,"/")}`,DJANGO_SECRET_KEY:process.env.DJANGO_SECRET_KEY||"cafino-electron-dev-runtime",DJANGO_DEBUG:"0",DJANGO_ALLOWED_HOSTS:"127.0.0.1,localhost",DJANGO_SECURE_SSL_REDIRECT:"0",CAF_INO_ENV:"local"};}
function runtimeExec(args=[]){
  if(app.isPackaged){const exe=packagedBackend();if(!fs.existsSync(exe))return null;return spawnSync(exe,args,{env:backendEnv(),encoding:"utf8",windowsHide:true});}
  const py=devPython(),server=path.join(devBackendDir(),"local_server.py");if(!fs.existsSync(py)||!fs.existsSync(server))return null;
  return spawnSync(py,[server,...args],{cwd:devBackendDir(),env:devEnv(),encoding:"utf8",windowsHide:true});
}
function parseResult(result,fallback){
  if(!result)return{ok:false,error:fallback||"Local runtime unavailable"};
  const lines=String(result.stdout||"").trim().split(/\r?\n/).filter(Boolean);
  for(let i=lines.length-1;i>=0;i--){try{return JSON.parse(lines[i])}catch{}}
  return{ok:false,error:String(result.stderr||fallback||"Command failed").trim(),status:result.status};
}
function verifiedBackup(target){const result=parseResult(runtimeExec(["--backup",target]),"Backup failed");return result&&result.ok?result:{...result,ok:false};}
function loadConfig(){
  const defaults={updateUrl:"",enforceLicense:false,licensePublicKey:"",backupIntervalHours:24,backupRetentionCount:14,backupMaxAgeDays:60};
  const file=app.isPackaged?path.join(process.resourcesPath,"config","release-config.json"):path.resolve(__dirname,"../release-config.dev.json");
  try{return{...defaults,...JSON.parse(fs.readFileSync(file,"utf8")),_file:file}}catch{return{...defaults,_file:file}}
}
function publicKeyPem(){
  const configured=String(releaseConfig?.licensePublicKey||"").trim();if(!configured)return"";
  const file=path.isAbsolute(configured)?configured:(app.isPackaged?path.join(process.resourcesPath,configured):path.resolve(__dirname,"..",configured));
  try{return fs.readFileSync(file,"utf8")}catch{return""}
}
function windowsMachineGuid(){
  if(process.platform!=="win32")return"";
  const r=spawnSync("reg.exe",["query","HKLM\\SOFTWARE\\Microsoft\\Cryptography","/v","MachineGuid"],{encoding:"utf8",windowsHide:true});
  if(r.status!==0)return"";const m=String(r.stdout||"").match(/MachineGuid\s+REG_SZ\s+([^\r\n]+)/i);return m?m[1].trim():"";
}
function machineIdentity(){return windowsMachineGuid()||license.fallbackMachineIdentity();}
function licenseFile(){return path.join(dataDir(),"license.json");}
function currentLicenseStatus(){
  const machine_hash=license.machineHash(machineIdentity());const key=publicKeyPem();const doc=license.loadLicense(licenseFile());
  const verification=license.verifyLicenseDocument(doc,key,machine_hash);
  return{enforced:!!releaseConfig?.enforceLicense,installed:!!doc,machine_hash,request_code:license.requestCode({machine_hash,version:app.getVersion()}),...verification};
}
async function importLicenseInteractive(){
  const selected=await dialog.showOpenDialog({title:"Import Cafino License",properties:["openFile"],filters:[{name:"Cafino License",extensions:["json","license"]}]});
  if(selected.canceled||!selected.filePaths[0])return{ok:false,canceled:true};
  let doc;try{doc=JSON.parse(fs.readFileSync(selected.filePaths[0],"utf8"))}catch{return{ok:false,reason:"invalid_json"}};
  const status=license.verifyLicenseDocument(doc,publicKeyPem(),license.machineHash(machineIdentity()));if(!status.ok)return status;
  license.saveLicense(licenseFile(),doc);return currentLicenseStatus();
}
async function enforceLicense(){
  if(!releaseConfig.enforceLicense)return true;
  for(;;){
    const status=currentLicenseStatus();if(status.ok)return true;
    const result=await dialog.showMessageBox({type:"warning",title:"Cafino License",message:"لایسنس معتبر Cafino Local روی این دستگاه نصب نیست.",detail:`وضعیت: ${status.reason||"unknown"}\nRequest Code: ${status.request_code}`,buttons:["Import License","Copy Request Code","Exit"],defaultId:0,cancelId:2,noLink:true});
    if(result.response===0){const imported=await importLicenseInteractive();if(imported.ok)return true;continue;}
    if(result.response===1){clipboard.writeText(status.request_code);continue;}
    app.quit();return false;
  }
}
function backupPolicy(){return{keepCount:releaseConfig.backupRetentionCount,maxAgeDays:releaseConfig.backupMaxAgeDays};}
function prune(){return ops.pruneBackups(ops.backupDirectory(dataDir()),backupPolicy());}
function autoBackup(force=false){
  const dir=ops.backupDirectory(dataDir());if(!fs.existsSync(dbPath()))return{ok:false,skipped:true,reason:"database_missing"};
  if(!force&&!ops.scheduledBackupDue(dir,{intervalHours:releaseConfig.backupIntervalHours}))return{ok:true,skipped:true,reason:"not_due"};
  const target=ops.scheduledBackupPath(dataDir());const result=verifiedBackup(target);if(result.ok)prune();return{...result,path:target};
}
function prepareUpdate(version){
  const target=ops.preUpdateBackupPath(dataDir(),version);const result=verifiedBackup(target);if(!result.ok)return result;
  const journal=ops.writeUpdateJournal(dataDir(),{from_version:app.getVersion(),to_version:String(version||""),backup_path:target,backup_sha256:result.sha256||""});prune();return{ok:true,backup:result,journal};
}
async function waitHealthy(){
  for(let i=0;i<90;i++){try{const r=await fetch("http://127.0.0.1:8000/api/v1/health/");if(r.ok)return true}catch{}await new Promise(r=>setTimeout(r,1000));}return false;
}
async function finalizePendingUpdate(){
  const journal=ops.readUpdateJournal(dataDir());if(!journal||journal.state!=="prepared")return;
  if(String(journal.to_version||"")!==app.getVersion())return;
  const healthy=await waitHealthy();
  if(healthy){ops.updateJournal(dataDir(),{state:"healthy",healthy_at:new Date().toISOString()});return;}
  ops.updateJournal(dataDir(),{state:"recovery_required",failed_at:new Date().toISOString()});
  await dialog.showMessageBox({type:"error",title:"Cafino Update Recovery",message:"نسخه جدید سلامت Backend را تأیید نکرد.",detail:`Backup قبل از آپدیت حفظ شده است:\n${journal.backup_path}\n\nبرای rollback کامل ابتدا installer امضاشده نسخه ${journal.from_version} را نصب کنید و سپس همین Backup را از بخش Backup/Restore برگردانید.`,buttons:["OK"]});
}
function setUpdateState(patch){updateState={...updateState,...patch,updated_at:new Date().toISOString()};return updateState;}
function initUpdater(){
  if(!app.isPackaged){setUpdateState({enabled:false,status:"development"});return;}
  updater=createUpdater({url:releaseConfig.updateUrl});if(!updater){setUpdateState({enabled:false,status:"not_configured"});return;}
  setUpdateState({enabled:true,status:"idle",url:releaseConfig.updateUrl});
  updater.on("checking-for-update",()=>setUpdateState({status:"checking"}));
  updater.on("update-not-available",info=>setUpdateState({status:"current",version:info?.version||app.getVersion()}));
  updater.on("update-available",info=>setUpdateState({status:"available",version:info?.version||""}));
  updater.on("download-progress",p=>setUpdateState({status:"downloading",percent:Math.round(p?.percent||0)}));
  updater.on("update-downloaded",info=>setUpdateState({status:"downloaded",version:info?.version||""}));
  updater.on("error",error=>setUpdateState({status:"error",error:String(error?.message||error)}));
}
async function checkUpdate(){if(!updater)return updateState;try{await updater.checkForUpdates();return updateState}catch(error){return setUpdateState({status:"error",error:String(error?.message||error)})}}
async function downloadUpdate(){if(!updater)return updateState;try{await updater.downloadUpdate();return updateState}catch(error){return setUpdateState({status:"error",error:String(error?.message||error)})}}
function installDownloadedUpdate(){
  if(!updater||updateState.status!=="downloaded")return{ok:false,error:"No downloaded update"};
  const prepared=prepareUpdate(updateState.version);if(!prepared.ok)return prepared;
  setUpdateState({status:"installing"});setImmediate(()=>updater.quitAndInstall(false,true));return{ok:true,prepared};
}
function registerIpc(){
  ipcMain.handle("release:status",async()=>({version:app.getVersion(),config:{updateConfigured:!!releaseConfig.updateUrl,enforceLicense:!!releaseConfig.enforceLicense,backupIntervalHours:releaseConfig.backupIntervalHours,backupRetentionCount:releaseConfig.backupRetentionCount,backupMaxAgeDays:releaseConfig.backupMaxAgeDays},license:currentLicenseStatus(),update:updateState,pending_update:ops.readUpdateJournal(dataDir()),backups:ops.listBackups(ops.backupDirectory(dataDir())).slice(0,20)}));
  ipcMain.handle("license:import",async()=>importLicenseInteractive());
  ipcMain.handle("license:requestCode",async()=>currentLicenseStatus());
  ipcMain.handle("backup:autoNow",async()=>autoBackup(true));
  ipcMain.handle("update:check",async()=>checkUpdate());
  ipcMain.handle("update:download",async()=>downloadUpdate());
  ipcMain.handle("update:install",async()=>installDownloadedUpdate());
}
function install(){
  app.whenReady().then(async()=>{
    releaseConfig=loadConfig();registerIpc();
    const licensed=await enforceLicense();if(!licensed)return;
    autoBackup(false);scheduleTimer=setInterval(()=>autoBackup(false),60*60*1000);
    initUpdater();setTimeout(()=>checkUpdate(),30000);setTimeout(()=>finalizePendingUpdate(),5000);
  });
  app.on("before-quit",()=>{if(scheduleTimer)clearInterval(scheduleTimer)});
}

module.exports={install,loadConfig,currentLicenseStatus,autoBackup,prepareUpdate};

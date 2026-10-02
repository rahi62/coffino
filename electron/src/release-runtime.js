const {app,dialog,clipboard,ipcMain}=require("electron");
const {spawnSync}=require("child_process");
const fs=require("fs");
const path=require("path");
const crypto=require("crypto");
const {createUpdater}=require("./updater");
const license=require("./offline-license");
const ops=require("./release-ops");
const opsClient=require("./ops-client");
const deviceAdapters=require("./device-adapters");

let updater=null;
let updateState={enabled:false,status:"disabled"};
let operationsState={enabled:false,status:"disabled",policy:null,lastHeartbeatAt:null,error:""};
let scheduleTimer=null;
let operationsTimer=null;
let releaseConfig=null;
let warnedBlockedVersion="";

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
  const defaults={updateUrl:"",releaseChannel:"stable",enforceLicense:false,licensePublicKey:"",backupIntervalHours:24,backupRetentionCount:14,backupMaxAgeDays:60,opsEndpoint:"",operationsEnabled:false,telemetryEnabled:false,heartbeatIntervalMinutes:60};
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
function importLicenseSync(){
  const files=dialog.showOpenDialogSync({title:"Import Cafino License",properties:["openFile"],filters:[{name:"Cafino License",extensions:["json","license"]}]});
  if(!files||!files[0])return{ok:false,canceled:true};
  let doc;try{doc=JSON.parse(fs.readFileSync(files[0],"utf8"))}catch{return{ok:false,reason:"invalid_json"}};
  const status=license.verifyLicenseDocument(doc,publicKeyPem(),license.machineHash(machineIdentity()));if(!status.ok)return status;
  license.saveLicense(licenseFile(),doc);return currentLicenseStatus();
}
async function importLicenseInteractive(){return importLicenseSync();}
function enforceLicenseSync(){
  if(!releaseConfig.enforceLicense)return true;
  for(;;){
    const status=currentLicenseStatus();if(status.ok)return true;
    const response=dialog.showMessageBoxSync({type:"warning",title:"Cafino License",message:"لایسنس معتبر Cafino Local روی این دستگاه نصب نیست.",detail:`وضعیت: ${status.reason||"unknown"}\nRequest Code: ${status.request_code}`,buttons:["Import License","Copy Request Code","Exit"],defaultId:0,cancelId:2,noLink:true});
    if(response===0){const imported=importLicenseSync();if(imported.ok)return true;continue;}
    if(response===1){clipboard.writeText(status.request_code);continue;}
    app.exit(0);return false;
  }
}
function backupPolicy(){return{keepCount:releaseConfig.backupRetentionCount,maxAgeDays:releaseConfig.backupMaxAgeDays};}
function prune(){return ops.pruneBackups(ops.backupDirectory(dataDir()),backupPolicy());}
function latestBackupSummary(){
  const rows=ops.listBackups(ops.backupDirectory(dataDir()));const latest=rows[0]||null;
  return{count:rows.length,latest,ageHours:latest?Math.max(0,(Date.now()-latest.mtimeMs)/3600000):null};
}
async function reportOpsEvent(event){
  if(!releaseConfig?.operationsEnabled||!releaseConfig?.telemetryEnabled||!opsClient.normalizeEndpoint(releaseConfig.opsEndpoint))return;
  try{
    await ensureOpsRegistration();
    await opsClient.sendEvent({userData:dataDir(),endpoint:releaseConfig.opsEndpoint,event:{...event,app_version:app.getVersion(),occurred_at:new Date().toISOString()}});
  }catch(error){operationsState={...operationsState,error:String(error?.message||error)}}
}
function autoBackup(force=false){
  const dir=ops.backupDirectory(dataDir());if(!fs.existsSync(dbPath()))return{ok:false,skipped:true,reason:"database_missing"};
  if(!force&&!ops.scheduledBackupDue(dir,{intervalHours:releaseConfig.backupIntervalHours}))return{ok:true,skipped:true,reason:"not_due"};
  const target=ops.scheduledBackupPath(dataDir());const result=verifiedBackup(target);
  if(result.ok)prune();else reportOpsEvent({event_type:"backup_failed",severity:"error",component:"backup",code:"verified_backup_failed"});
  return{...result,path:target};
}
function prepareUpdate(version){
  const target=ops.preUpdateBackupPath(dataDir(),version);const result=verifiedBackup(target);if(!result.ok)return result;
  const journal=ops.writeUpdateJournal(dataDir(),{from_version:app.getVersion(),to_version:String(version||""),backup_path:target,backup_sha256:result.sha256||""});prune();return{ok:true,backup:result,journal};
}
async function backendHealthy(){try{const r=await fetch("http://127.0.0.1:8000/api/v1/health/",{signal:AbortSignal.timeout(2500)});return r.ok}catch{return false}}
async function waitHealthy(){for(let i=0;i<90;i++){if(await backendHealthy())return true;await new Promise(r=>setTimeout(r,1000));}return false;}
async function finalizePendingUpdate(){
  const journal=ops.readUpdateJournal(dataDir());if(!journal||journal.state!=="prepared")return;
  if(String(journal.to_version||"")!==app.getVersion())return;
  const healthy=await waitHealthy();
  if(healthy){ops.updateJournal(dataDir(),{state:"healthy",healthy_at:new Date().toISOString()});await reportOpsEvent({event_type:"update_success",severity:"info",component:"updater",code:"post_update_healthy"});return;}
  ops.updateJournal(dataDir(),{state:"recovery_required",failed_at:new Date().toISOString()});
  await reportOpsEvent({event_type:"recovery_required",severity:"critical",component:"updater",code:"post_update_health_failed"});
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
  updater.on("error",error=>{setUpdateState({status:"error",error:String(error?.message||error)});reportOpsEvent({event_type:"update_failed",severity:"error",component:"updater",code:"electron_updater_error"})});
}
function opsConfigured(){return !!(releaseConfig?.operationsEnabled&&opsClient.normalizeEndpoint(releaseConfig?.opsEndpoint));}
async function ensureOpsRegistration(){
  if(!opsConfigured())throw new Error("operations_not_configured");
  const status=currentLicenseStatus();const document=license.loadLicense(licenseFile());
  if(!status.ok||!document)throw new Error("valid_license_required_for_operations");
  const result=await opsClient.ensureRegistered({userData:dataDir(),endpoint:releaseConfig.opsEndpoint,licenseDocument:document,machineHash:status.machine_hash,version:app.getVersion(),channel:releaseConfig.releaseChannel||"stable",platform:process.platform,arch:process.arch,telemetryEnabled:!!releaseConfig.telemetryEnabled});
  return result;
}
async function collectDiagnosticSnapshot(){
  const backups=latestBackupSummary();const registry=deviceAdapters.registryPayload(process.env);let freeDisk=0;
  try{const stat=fs.statfsSync(dataDir());freeDisk=Number(stat.bavail)*Number(stat.bsize)}catch{}
  const groups=registry.groups||{};
  return{
    app_version:app.getVersion(),release_channel:releaseConfig.releaseChannel||"stable",platform:process.platform,arch:process.arch,
    backend_healthy:await backendHealthy(),uptime_seconds:Math.round(process.uptime()),db_size_bytes:fs.existsSync(dbPath())?fs.statSync(dbPath()).size:0,
    free_disk_bytes:Math.max(0,freeDisk),backup_count:backups.count,latest_backup_age_hours:backups.ageHours,
    update_status:String(updateState.status||"").slice(0,32),adapter_printer:String(groups.PRINTER?.selected||"").slice(0,32),adapter_pager:String(groups.PAGER?.selected||"").slice(0,32),adapter_pos:String(groups.POS?.selected||"").slice(0,32),
  };
}
async function heartbeatOperations(){
  if(!opsConfigured()){operationsState={enabled:false,status:"disabled",policy:null,lastHeartbeatAt:null,error:""};return operationsState;}
  operationsState={...operationsState,enabled:true,status:"connecting",error:""};
  try{
    await ensureOpsRegistration();const backups=latestBackupSummary();
    const response=await opsClient.heartbeat({userData:dataDir(),endpoint:releaseConfig.opsEndpoint,payload:{current_version:app.getVersion(),channel:releaseConfig.releaseChannel||"stable",platform:process.platform,arch:process.arch,app_health:(await backendHealthy())?"healthy":"degraded",telemetry_enabled:!!releaseConfig.telemetryEnabled,last_backup_at:backups.latest?new Date(backups.latest.mtimeMs).toISOString():null,last_backup_ok:backups.latest?true:null,last_update_status:String(updateState.status||"").slice(0,32)}});
    operationsState={enabled:true,status:"online",policy:response.policy||null,lastHeartbeatAt:new Date().toISOString(),error:""};
    if(response.diagnostic_request_id){const snapshot=await collectDiagnosticSnapshot();await opsClient.submitDiagnostic({userData:dataDir(),endpoint:releaseConfig.opsEndpoint,requestId:response.diagnostic_request_id,snapshot});operationsState.lastDiagnosticAt=new Date().toISOString();}
    const policy=response.policy||{};
    if(policy.current_blocked&&warnedBlockedVersion!==app.getVersion()){
      warnedBlockedVersion=app.getVersion();
      dialog.showMessageBox({type:"warning",title:"Cafino Release Safety",message:"نسخه فعلی Cafino در Release Control علامت‌گذاری شده است.",detail:`عملیات اصلی Local متوقف نمی‌شود. ${policy.advisory_message||"برای نصب نسخه امن بعدی یا rollback با پشتیبانی هماهنگ کنید."}`,buttons:["OK"]});
    }
    return operationsState;
  }catch(error){operationsState={...operationsState,enabled:true,status:"offline",error:String(error?.message||error)};return operationsState;}
}
async function checkUpdate(){
  if(!updater)return updateState;
  if(opsConfigured()){
    await heartbeatOperations();const policy=operationsState.policy;
    if(policy?.managed){
      if(policy.target_version===app.getVersion())return setUpdateState({status:"current",version:app.getVersion(),managedByOps:true});
      if(!policy.update_allowed){
        const status=policy.current_blocked?"blocked_version":policy.paused?"rollout_paused":"rollout_wait";
        return setUpdateState({status,managedByOps:true,policyTarget:policy.target_version||"",error:policy.current_blocked?(policy.advisory_message||"Current version is blocked by release policy"):""});
      }
    }
  }
  try{await updater.checkForUpdates();return updateState}catch(error){return setUpdateState({status:"error",error:String(error?.message||error)})}
}
async function downloadUpdate(){if(!updater)return updateState;try{await updater.downloadUpdate();return updateState}catch(error){return setUpdateState({status:"error",error:String(error?.message||error)})}}
function installDownloadedUpdate(){
  if(!updater||updateState.status!=="downloaded")return{ok:false,error:"No downloaded update"};
  const prepared=prepareUpdate(updateState.version);if(!prepared.ok)return prepared;
  setUpdateState({status:"installing"});setImmediate(()=>updater.quitAndInstall(false,true));return{ok:true,prepared};
}
function registerIpc(){
  ipcMain.handle("release:status",async()=>({version:app.getVersion(),config:{updateConfigured:!!releaseConfig.updateUrl,enforceLicense:!!releaseConfig.enforceLicense,backupIntervalHours:releaseConfig.backupIntervalHours,backupRetentionCount:releaseConfig.backupRetentionCount,backupMaxAgeDays:releaseConfig.backupMaxAgeDays,operationsConfigured:opsConfigured(),telemetryEnabled:!!releaseConfig.telemetryEnabled},license:currentLicenseStatus(),update:updateState,operations:operationsState,pending_update:ops.readUpdateJournal(dataDir()),backups:ops.listBackups(ops.backupDirectory(dataDir())).slice(0,20)}));
  ipcMain.handle("license:import",async()=>importLicenseInteractive());
  ipcMain.handle("license:requestCode",async()=>currentLicenseStatus());
  ipcMain.handle("backup:autoNow",async()=>autoBackup(true));
  ipcMain.handle("update:check",async()=>checkUpdate());
  ipcMain.handle("update:download",async()=>downloadUpdate());
  ipcMain.handle("update:install",async()=>installDownloadedUpdate());
  ipcMain.handle("operations:sync",async()=>heartbeatOperations());
}
function install(){
  app.on("ready",()=>{
    releaseConfig=loadConfig();registerIpc();
    if(!enforceLicenseSync())return;
    autoBackup(false);scheduleTimer=setInterval(()=>autoBackup(false),60*60*1000);
    initUpdater();
    if(opsConfigured()){
      setTimeout(()=>heartbeatOperations(),10000);
      operationsTimer=setInterval(()=>heartbeatOperations(),Math.max(15,Number(releaseConfig.heartbeatIntervalMinutes||60))*60*1000);
      process.on("uncaughtExceptionMonitor",error=>reportOpsEvent({event_type:"crash",severity:"critical",component:"electron",code:"uncaught_exception",fingerprint:opsClient.fingerprintError(error,"electron")}));
    }
    setTimeout(()=>checkUpdate(),30000);setTimeout(()=>finalizePendingUpdate(),5000);
  });
  app.on("before-quit",()=>{if(scheduleTimer)clearInterval(scheduleTimer);if(operationsTimer)clearInterval(operationsTimer)});
}

module.exports={install,loadConfig,currentLicenseStatus,autoBackup,prepareUpdate,enforceLicenseSync,heartbeatOperations,collectDiagnosticSnapshot};

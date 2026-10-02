const fs=require("fs");
const path=require("path");

function ensureDir(dir){fs.mkdirSync(dir,{recursive:true});return dir;}
function safeInt(value,fallback,min=1,max=10000){const n=Number.parseInt(String(value??""),10);return Number.isFinite(n)&&n>=min&&n<=max?n:fallback;}
function backupDirectory(dataDir){return ensureDir(path.join(dataDir,"backups"));}
function updateDirectory(dataDir){return ensureDir(path.join(dataDir,"updates"));}
function stamp(date=new Date()){return date.toISOString().replace(/[-:]/g,"").replace(/\.\d{3}Z$/,"Z");}
function scheduledBackupPath(dataDir,date=new Date()){return path.join(backupDirectory(dataDir),`cafino-auto-${stamp(date)}.sqlite3`);}
function preUpdateBackupPath(dataDir,version,date=new Date()){const safe=String(version||"unknown").replace(/[^0-9A-Za-z._-]/g,"_");return path.join(backupDirectory(dataDir),`cafino-pre-update-${safe}-${stamp(date)}.sqlite3`);}
function listBackups(dir){
  if(!fs.existsSync(dir))return[];
  return fs.readdirSync(dir).filter(name=>/^cafino-(?:auto|pre-update)-.+\.sqlite3$/i.test(name)).map(name=>{
    const full=path.join(dir,name);const stat=fs.statSync(full);return{name,path:full,mtimeMs:stat.mtimeMs,size:stat.size};
  }).sort((a,b)=>b.mtimeMs-a.mtimeMs);
}
function pruneBackups(dir,{keepCount=14,maxAgeDays=60,now=Date.now()}={}){
  const keep=safeInt(keepCount,14,1,500);const days=safeInt(maxAgeDays,60,1,3650);const maxAgeMs=days*86400000;
  const backups=listBackups(dir);const removed=[];
  backups.forEach((entry,index)=>{if(index>=keep||now-entry.mtimeMs>maxAgeMs){try{fs.unlinkSync(entry.path);removed.push(entry.path)}catch{}}});
  return{kept:listBackups(dir),removed};
}
function latestScheduledBackup(dir){return listBackups(dir).find(x=>/^cafino-auto-/i.test(x.name))||null;}
function scheduledBackupDue(dir,{intervalHours=24,now=Date.now()}={}){const hours=safeInt(intervalHours,24,1,24*30);const latest=latestScheduledBackup(dir);return!latest||now-latest.mtimeMs>=hours*3600000;}
function writeJsonAtomic(file,data){ensureDir(path.dirname(file));const tmp=`${file}.tmp-${process.pid}-${Date.now()}`;fs.writeFileSync(tmp,JSON.stringify(data,null,2),"utf8");fs.renameSync(tmp,file);return file;}
function readJson(file){try{return JSON.parse(fs.readFileSync(file,"utf8"))}catch{return null}}
function journalPath(dataDir){return path.join(updateDirectory(dataDir),"pending-update.json");}
function writeUpdateJournal(dataDir,data){const payload={schema:1,state:"prepared",prepared_at:new Date().toISOString(),...data};writeJsonAtomic(journalPath(dataDir),payload);return payload;}
function readUpdateJournal(dataDir){return readJson(journalPath(dataDir));}
function updateJournal(dataDir,patch){const current=readUpdateJournal(dataDir)||{schema:1};const next={...current,...patch,updated_at:new Date().toISOString()};writeJsonAtomic(journalPath(dataDir),next);return next;}
function clearUpdateJournal(dataDir){const file=journalPath(dataDir);try{fs.unlinkSync(file);return true}catch(error){return error&&error.code==="ENOENT"}}

module.exports={ensureDir,safeInt,backupDirectory,updateDirectory,scheduledBackupPath,preUpdateBackupPath,listBackups,pruneBackups,latestScheduledBackup,scheduledBackupDue,writeJsonAtomic,readJson,journalPath,writeUpdateJournal,readUpdateJournal,updateJournal,clearUpdateJournal};

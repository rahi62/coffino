const assert=require("assert");
const fs=require("fs");
const os=require("os");
const path=require("path");
const ops=require("./release-ops");

function touch(file,mtimeMs){fs.mkdirSync(path.dirname(file),{recursive:true});fs.writeFileSync(file,"db");const d=new Date(mtimeMs);fs.utimesSync(file,d,d);}

const root=fs.mkdtempSync(path.join(os.tmpdir(),"cafino-release-ops-"));
try{
  const dir=ops.backupDirectory(root);const now=Date.now();
  for(let i=0;i<5;i++)touch(path.join(dir,`cafino-auto-2026010${i}T000000Z.sqlite3`),now-i*86400000);
  touch(path.join(dir,"ignore.txt"),now);
  const pruned=ops.pruneBackups(dir,{keepCount:3,maxAgeDays:30,now});
  assert.strictEqual(pruned.kept.length,3);
  assert.strictEqual(pruned.removed.length,2);
  assert.strictEqual(fs.existsSync(path.join(dir,"ignore.txt")),true);
  assert.strictEqual(ops.scheduledBackupDue(dir,{intervalHours:12,now}),false);
  assert.strictEqual(ops.scheduledBackupDue(dir,{intervalHours:12,now:now+13*3600000}),true);

  const journal=ops.writeUpdateJournal(root,{from_version:"1.0.0",to_version:"1.1.0",backup_path:"x.sqlite3"});
  assert.strictEqual(journal.state,"prepared");
  assert.strictEqual(ops.readUpdateJournal(root).to_version,"1.1.0");
  ops.updateJournal(root,{state:"healthy"});
  assert.strictEqual(ops.readUpdateJournal(root).state,"healthy");
  assert.strictEqual(ops.clearUpdateJournal(root),true);
  assert.strictEqual(ops.readUpdateJournal(root),null);
  console.log("release-ops tests passed");
}finally{fs.rmSync(root,{recursive:true,force:true});}

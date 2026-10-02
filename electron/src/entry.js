const {app}=require("electron");
const fs=require("fs");
const path=require("path");

function runSmokeCheck(){
  const output=String(process.env.CAF_INO_SMOKE_OUTPUT||"").trim();
  const result={ok:false,version:app.getVersion(),packaged:app.isPackaged,checks:{}};
  try{
    if(!app.isPackaged)throw new Error("Smoke check requires packaged app");
    const resources=process.resourcesPath;
    const backend=path.join(resources,"backend","cafino-backend.exe");
    const frontend=path.join(resources,"frontend","server.js");
    const configPath=path.join(resources,"config","release-config.json");
    result.checks.backend=fs.existsSync(backend);
    result.checks.frontend=fs.existsSync(frontend);
    result.checks.config=fs.existsSync(configPath);
    if(!result.checks.backend||!result.checks.frontend||!result.checks.config)throw new Error("Packaged runtime resources are incomplete");
    const config=JSON.parse(fs.readFileSync(configPath,"utf8"));
    result.channel=config.releaseChannel||"stable";
    result.updateUrl=config.updateUrl||"";
    result.enforceLicense=!!config.enforceLicense;
    result.operationsEnabled=!!config.operationsEnabled;
    result.telemetryEnabled=!!config.telemetryEnabled;
    result.checks.channel=["stable","beta"].includes(result.channel);
    result.checks.httpsUpdate=!result.updateUrl||result.updateUrl.startsWith("https://");
    result.checks.operationsEndpoint=!result.operationsEnabled||(typeof config.opsEndpoint==="string"&&config.opsEndpoint.startsWith("https://"));
    result.checks.telemetryRequiresOperations=!result.telemetryEnabled||result.operationsEnabled;
    result.checks.heartbeatInterval=Number(config.heartbeatIntervalMinutes||60)>=15;
    if(result.enforceLicense){
      const key=path.join(resources,String(config.licensePublicKey||""));
      result.checks.licensePublicKey=!!config.licensePublicKey&&fs.existsSync(key);
    }else result.checks.licensePublicKey=true;
    result.ok=Object.values(result.checks).every(Boolean);
    if(!result.ok)throw new Error("One or more package checks failed");
  }catch(error){result.error=String(error?.message||error)}
  if(output){fs.mkdirSync(path.dirname(output),{recursive:true});fs.writeFileSync(output,JSON.stringify(result,null,2),"utf8")}
  app.exit(result.ok?0:2);
}

if(process.argv.includes("--cafino-smoke-check")){
  app.whenReady().then(runSmokeCheck);
}else{
  require("./release-runtime").install();
  require("./main");
}

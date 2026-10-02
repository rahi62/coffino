const crypto=require("crypto");
const fs=require("fs");
const path=require("path");

function normalizeEndpoint(value){
  const raw=String(value||"").trim();if(!raw)return"";
  let url;try{url=new URL(raw)}catch{return""}
  if(url.protocol!=="https:")return"";
  return url.toString().replace(/\/$/,"");
}
function stateFile(userData){return path.join(userData,"ops-device.json");}
function loadState(userData){
  const file=stateFile(userData);let state={installation_id:crypto.randomUUID(),device_token:""};
  try{state={...state,...JSON.parse(fs.readFileSync(file,"utf8"))}}catch{}
  if(!state.installation_id)state.installation_id=crypto.randomUUID();
  saveState(userData,state);return state;
}
function saveState(userData,state){
  fs.mkdirSync(userData,{recursive:true});
  fs.writeFileSync(stateFile(userData),JSON.stringify({installation_id:state.installation_id,device_token:state.device_token||""},null,2),{encoding:"utf8",mode:0o600});
  return state;
}
function clearToken(userData){const state=loadState(userData);state.device_token="";saveState(userData,state);return state;}
async function request(endpoint,route,{method="GET",token="",body=null,timeoutMs=7000}={}){
  const base=normalizeEndpoint(endpoint);if(!base)throw new Error("invalid_ops_endpoint");
  const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),timeoutMs);
  try{
    const response=await fetch(`${base}${route}`,{method,headers:{Accept:"application/json",...(body?{"Content-Type":"application/json"}:{}),...(token?{Authorization:`Bearer ${token}`}:{})},body:body?JSON.stringify(body):undefined,signal:controller.signal});
    let data={};try{data=await response.json()}catch{}
    if(!response.ok){const error=new Error(data?.detail||`ops_http_${response.status}`);error.status=response.status;throw error;}
    return data;
  }finally{clearTimeout(timer)}
}
async function ensureRegistered({userData,endpoint,licenseDocument,machineHash,version,channel,platform,arch,telemetryEnabled}){
  const state=loadState(userData);if(state.device_token)return state;
  if(!licenseDocument||!machineHash)throw new Error("license_required_for_ops_registration");
  const data=await request(endpoint,"/register/",{method:"POST",body:{license_document:licenseDocument,machine_hash:machineHash,installation_id:state.installation_id,current_version:version,channel,platform,arch,telemetry_enabled:!!telemetryEnabled}});
  state.device_token=data.device_token||"";if(!state.device_token)throw new Error("ops_registration_missing_token");
  saveState(userData,state);return{...state,registration:data};
}
async function heartbeat({userData,endpoint,payload}){
  const state=loadState(userData);if(!state.device_token)throw new Error("ops_not_registered");
  try{return await request(endpoint,"/heartbeat/",{method:"POST",token:state.device_token,body:payload})}
  catch(error){if(error.status===401)clearToken(userData);throw error}
}
async function policy({userData,endpoint}){
  const state=loadState(userData);if(!state.device_token)throw new Error("ops_not_registered");
  try{return await request(endpoint,"/policy/",{token:state.device_token})}
  catch(error){if(error.status===401)clearToken(userData);throw error}
}
async function sendEvent({userData,endpoint,event}){
  const state=loadState(userData);if(!state.device_token)throw new Error("ops_not_registered");
  try{return await request(endpoint,"/events/",{method:"POST",token:state.device_token,body:event})}
  catch(error){if(error.status===401)clearToken(userData);throw error}
}
async function submitDiagnostic({userData,endpoint,requestId,snapshot}){
  const state=loadState(userData);if(!state.device_token)throw new Error("ops_not_registered");
  try{return await request(endpoint,"/diagnostics/",{method:"POST",token:state.device_token,body:{request_id:requestId,snapshot}})}
  catch(error){if(error.status===401)clearToken(userData);throw error}
}
function fingerprintError(error,component="electron"){
  const name=String(error?.name||"Error").slice(0,80);
  const stack=String(error?.stack||"").split(/\r?\n/).slice(1,4).map(line=>line.replace(/[A-Za-z]:\\[^\s)]+/g,"<path>").replace(/\/[^\s)]+/g,"<path>")).join("|");
  return crypto.createHash("sha256").update(`${component}|${name}|${stack}`).digest("hex");
}

module.exports={normalizeEndpoint,loadState,saveState,clearToken,request,ensureRegistered,heartbeat,policy,sendEvent,submitDiagnostic,fingerprintError};

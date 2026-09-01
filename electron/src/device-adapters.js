const fs=require("fs");
const net=require("net");
const os=require("os");
const path=require("path");
const {execFile}=require("child_process");

const ADAPTERS={
  PRINTER:[
    {key:"SYSTEM",label:"System printer",status:"ready",mode:"native",description:"Electron/Windows system printer"},
  ],
  PAGER:[
    {key:"NONE",label:"No pager adapter",status:"unconfigured",mode:"none",description:"Pager hardware is not configured"},
    {key:"VENDOR_SDK",label:"Vendor pager SDK",status:"planned",mode:"sdk",description:"Requires the vendor SDK/bridge"},
  ],
  POS:[
    {key:"MANUAL",label:"Manual POS terminal",status:"manual",mode:"manual",description:"Operator enters the amount on the terminal"},
    {key:"HTTP_BRIDGE",label:"Local HTTP POS bridge",status:"configurable",mode:"bridge",description:"POSTs a sale request to a local/private vendor bridge"},
    {key:"TCP_JSON",label:"Local TCP JSON POS bridge",status:"configurable",mode:"bridge",description:"Sends one JSON request/response over a private TCP endpoint"},
    {key:"EXEC_BRIDGE",label:"Vendor helper executable",status:"configurable",mode:"bridge",description:"Runs a local vendor helper executable without a shell"},
    {key:"VENDOR_SDK",label:"Direct vendor SDK",status:"planned",mode:"sdk",description:"Implement only after receiving the exact PSP/vendor SDK"},
  ],
};

const posApprovalMemory=new Map();
const posApprovalInflight=new Map();

function selected(env,key,fallback){
  const raw=String(env[`CAF_INO_${key}_ADAPTER`]||env[`CAFINO_${key}_ADAPTER`]||fallback).trim().toUpperCase();
  return ADAPTERS[key].some(x=>x.key===raw)?raw:fallback;
}
function csv(v){return String(v||"").split(",").map(x=>x.trim().toLowerCase()).filter(Boolean)}
function privateIpv4(host){
  const m=String(host||"").match(/^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/);if(!m)return false;
  const p=m.slice(1).map(Number);if(p.some(x=>x<0||x>255))return false;
  return p[0]===10||p[0]===127||(p[0]===192&&p[1]===168)||(p[0]===172&&p[1]>=16&&p[1]<=31);
}
function allowedBridgeHost(host,env=process.env){
  const value=String(host||"").toLowerCase();
  if(value==="localhost"||value==="::1"||privateIpv4(value))return true;
  return csv(env.CAF_INO_POS_BRIDGE_ALLOW_HOSTS).includes(value);
}
function httpBridgeUrl(env=process.env){
  const raw=String(env.CAF_INO_POS_BRIDGE_URL||"").trim();if(!raw)return null;
  try{const u=new URL(raw);if(!["http:","https:"].includes(u.protocol)||!allowedBridgeHost(u.hostname,env))return null;return u}catch{return null}
}
function tcpBridgeConfig(env=process.env){
  const host=String(env.CAF_INO_POS_TCP_HOST||"").trim();const port=Number(env.CAF_INO_POS_TCP_PORT||0);
  return host&&Number.isInteger(port)&&port>0&&port<65536&&allowedBridgeHost(host,env)?{host,port}:null;
}
function execBridgePath(env=process.env){const p=String(env.CAF_INO_POS_EXECUTABLE||"").trim();return p&&fs.existsSync(p)?p:null}
function adapterRuntimeStatus(key,env=process.env){
  if(key==="HTTP_BRIDGE")return httpBridgeUrl(env)?"ready":"unconfigured";
  if(key==="TCP_JSON")return tcpBridgeConfig(env)?"ready":"unconfigured";
  if(key==="EXEC_BRIDGE")return execBridgePath(env)?"ready":"unconfigured";
  return ADAPTERS.POS.find(x=>x.key===key)?.status||"unconfigured";
}
function registryPayload(env=process.env){
  const printer=selected(env,"PRINTER","SYSTEM"),pager=selected(env,"PAGER","NONE"),pos=selected(env,"POS","MANUAL");
  const group=(key,value)=>({selected:value,adapters:ADAPTERS[key].map(x=>({...x,id:x.key,status:key==="POS"?adapterRuntimeStatus(x.key,env):x.status,selected:x.key===value}))});
  return{ok:true,groups:{PRINTER:group("PRINTER",printer),PAGER:group("PAGER",pager),POS:group("POS",pos)}};
}
function callPager(pager,env=process.env){
  const adapter=selected(env,"PAGER","NONE");
  if(adapter==="NONE")return{ok:false,status:"unconfigured",adapter,message:"Pager adapter is not configured."};
  return{ok:false,status:"planned",adapter,pager:String(pager?.number||pager||""),message:`${adapter} requires a vendor SDK/bridge implementation.`};
}
function saleInput(input,env=process.env){
  const raw=typeof input==="object"&&input!==null?input:{amount:input};
  const amount=Number(raw.amount);if(!Number.isSafeInteger(amount)||amount<=0)return null;
  const unit=String(env.CAF_INO_POS_AMOUNT_UNIT||"RIAL").trim().toUpperCase();
  let terminalAmount=amount;
  if(unit==="TOMAN"){
    if(amount%10!==0)return null;
    terminalAmount=amount/10;
  }else if(unit!=="RIAL")return null;
  const reference=String(raw.reference||"").replace(/[^A-Za-z0-9_.:-]/g,"").slice(0,80);
  return{amount,terminalAmount,currency:unit==="TOMAN"?"IRT":"IRR",reference,payerLabel:String(raw.payerLabel||"").slice(0,80)};
}
function safeText(value,max=120){return String(value??"").replace(/[\r\n\t]/g," ").slice(0,max)}
function maskedPan(value){const digits=String(value||"").replace(/\D/g,"");return digits.length>=4?`****${digits.slice(-4)}`:""}
function approvedValue(raw){
  if(raw?.approved===true||raw?.success===true)return true;
  const status=String(raw?.status||raw?.result||"").toLowerCase();return ["approved","success","succeeded","00"].includes(status);
}
function normalizeResponse(raw,adapter,sale){
  const approved=approvedValue(raw);const status=safeText(raw?.status||raw?.result||(approved?"approved":"declined"),32);
  return{ok:approved,approved,status,adapter,amount:sale.amount,terminalAmount:sale.terminalAmount,currency:sale.currency,
    referenceNumber:safeText(raw?.reference_number||raw?.referenceNumber||raw?.rrn||raw?.retrieval_reference||"",120),
    traceNumber:safeText(raw?.trace_number||raw?.traceNumber||raw?.trace||raw?.stan||"",80),
    terminalId:safeText(raw?.terminal_id||raw?.terminalId||raw?.tid||"",80),maskedPan:maskedPan(raw?.masked_pan||raw?.maskedPan||raw?.pan||""),
    message:safeText(raw?.message||raw?.description||(approved?"POS transaction approved.":"POS transaction was not approved."),180)};
}
function posJournalPath(env=process.env){
  const configured=String(env.CAF_INO_POS_JOURNAL_PATH||"").trim();
  if(configured)return path.resolve(configured);
  const base=String(env.APPDATA||"").trim()?path.join(env.APPDATA,"Cafino"):path.join(os.homedir(),".cafino");
  return path.join(base,"pos-approvals.ndjson");
}
function posJournalKey(journalPath,reference){return`${journalPath}\u0000${reference}`}
function ensurePosJournalReadable(env=process.env){
  const journalPath=posJournalPath(env),dir=path.dirname(journalPath);
  fs.mkdirSync(dir,{recursive:true});
  const handle=fs.openSync(journalPath,"a");fs.closeSync(handle);
  const text=fs.readFileSync(journalPath,"utf8");
  const ended=text.length===0||text.endsWith("\n");
  const rows=new Map(),lines=text.split(/\r?\n/);
  for(let i=0;i<lines.length;i++){
    const line=lines[i];if(!line.trim())continue;
    try{
      const row=JSON.parse(line);
      if(!row||row.version!==1||typeof row.reference!=="string"||!Number.isSafeInteger(row.amount)||!row.result?.approved)throw new Error("invalid_row");
      rows.set(row.reference,row);
    }catch(error){
      const isTrailingPartial=!ended&&i===lines.length-1;
      if(isTrailingPartial)break;
      throw new Error(`POS approval journal is unreadable at line ${i+1}; stop automatic POS payments and reconcile the journal before retrying.`);
    }
  }
  return{journalPath,rows};
}
function approvalSnapshot(result){
  return{
    ok:true,approved:true,status:safeText(result.status||"approved",32),adapter:safeText(result.adapter||"",32),
    amount:Number(result.amount),terminalAmount:Number(result.terminalAmount),currency:safeText(result.currency||"",8),
    referenceNumber:safeText(result.referenceNumber||"",120),traceNumber:safeText(result.traceNumber||"",80),
    terminalId:safeText(result.terminalId||"",80),maskedPan:maskedPan(result.maskedPan||""),
    message:safeText(result.message||"POS transaction approved.",180),
  };
}
function appendPosApproval(sale,result,env=process.env){
  const journalPath=posJournalPath(env);fs.mkdirSync(path.dirname(journalPath),{recursive:true});
  const row={version:1,reference:sale.reference,amount:sale.amount,approvedAt:new Date().toISOString(),result:approvalSnapshot(result)};
  fs.appendFileSync(journalPath,JSON.stringify(row)+"\n",{encoding:"utf8",mode:0o600});
  return row;
}
function cachedPosApproval(sale,env=process.env){
  const journalPath=posJournalPath(env),memoryKey=posJournalKey(journalPath,sale.reference);
  const memory=posApprovalMemory.get(memoryKey);
  if(memory){
    if(memory.amount!==sale.amount)return{conflict:true,message:"This POS reference was already approved for a different amount. Do not retry automatically."};
    return{result:{...memory.result,replayed:true,journal:"memory"}};
  }
  const {rows}=ensurePosJournalReadable(env),row=rows.get(sale.reference);
  if(!row)return{};
  if(row.amount!==sale.amount)return{conflict:true,message:"This POS reference already exists in the approval journal with a different amount. Do not retry automatically."};
  posApprovalMemory.set(memoryKey,row);
  return{result:{...row.result,replayed:true,journal:"disk"}};
}
async function httpSale(sale,env){
  const url=httpBridgeUrl(env);if(!url)throw new Error("POS HTTP bridge URL is missing or not local/private.");
  const timeout=Math.max(1000,Math.min(180000,Number(env.CAF_INO_POS_TIMEOUT_MS||90000)));const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),timeout);
  try{
    const token=String(env.CAF_INO_POS_BRIDGE_TOKEN||"").trim();const response=await fetch(url,{method:"POST",headers:{"Content-Type":"application/json",...(token?{Authorization:`Bearer ${token}`}:{})},body:JSON.stringify({amount:sale.terminalAmount,currency:sale.currency,reference:sale.reference,payer_label:sale.payerLabel}),signal:controller.signal,redirect:"error"});
    const text=await response.text();let data={};try{data=text?JSON.parse(text):{}}catch{throw new Error("POS bridge returned invalid JSON.")}
    if(!response.ok)return{...data,approved:false,success:false,ok:false,status:data.status||`http_${response.status}`,message:data.message||`POS bridge HTTP ${response.status}`};return data;
  }finally{clearTimeout(timer)}
}
function tcpSale(sale,env){return new Promise((resolve,reject)=>{
  const cfg=tcpBridgeConfig(env);if(!cfg)return reject(new Error("POS TCP bridge is not configured for a local/private host."));
  const timeout=Math.max(1000,Math.min(180000,Number(env.CAF_INO_POS_TIMEOUT_MS||90000)));const socket=net.createConnection(cfg);let buffer="";let done=false;
  const finish=(err,value)=>{if(done)return;done=true;socket.destroy();err?reject(err):resolve(value)};
  socket.setTimeout(timeout,()=>finish(new Error("POS TCP bridge timed out.")));socket.on("error",finish);
  socket.on("connect",()=>socket.write(JSON.stringify({amount:sale.terminalAmount,currency:sale.currency,reference:sale.reference,payer_label:sale.payerLabel})+"\n"));
  socket.on("data",chunk=>{buffer+=chunk.toString("utf8");if(buffer.length>65536)return finish(new Error("POS TCP response is too large."));const i=buffer.indexOf("\n");if(i>=0){try{finish(null,JSON.parse(buffer.slice(0,i)))}catch{finish(new Error("POS TCP bridge returned invalid JSON."))}}});
})}
function execSale(sale,env){return new Promise((resolve,reject)=>{
  const executable=execBridgePath(env);if(!executable)return reject(new Error("POS helper executable is not configured or does not exist."));
  const timeout=Math.max(1000,Math.min(180000,Number(env.CAF_INO_POS_TIMEOUT_MS||90000)));
  const args=["--amount",String(sale.terminalAmount),"--currency",sale.currency,"--reference",sale.reference];
  execFile(executable,args,{windowsHide:true,timeout,maxBuffer:64*1024},(error,stdout)=>{if(error)return reject(new Error(`POS helper failed: ${safeText(error.message,160)}`));try{resolve(JSON.parse(String(stdout||"").trim()))}catch{reject(new Error("POS helper returned invalid JSON."))}});
})}
async function directSale(sale,adapter,env){
  const raw=adapter==="HTTP_BRIDGE"?await httpSale(sale,env):adapter==="TCP_JSON"?await tcpSale(sale,env):adapter==="EXEC_BRIDGE"?await execSale(sale,env):null;
  if(!raw)return{ok:false,approved:false,adapter,status:"unconfigured",message:"POS adapter is not configured."};
  return normalizeResponse(raw,adapter,sale);
}
async function authorizeDirectPos(sale,adapter,env=process.env){
  if(!sale.reference)return{ok:false,approved:false,adapter,error:"missing_reference",message:"Automatic POS payments require a stable idempotency reference."};
  let cached;
  try{cached=cachedPosApproval(sale,env)}catch(error){return{ok:false,approved:false,adapter,error:"journal_unreadable",message:safeText(error?.message||error,220)}}
  if(cached.conflict)return{ok:false,approved:false,adapter,error:"reference_conflict",message:cached.message};
  if(cached.result)return cached.result;

  const journalPath=posJournalPath(env),inflightKey=posJournalKey(journalPath,sale.reference);
  if(posApprovalInflight.has(inflightKey))return posApprovalInflight.get(inflightKey);
  const task=(async()=>{
    const result=await directSale(sale,adapter,env);
    if(!result?.ok||!result?.approved)return result;
    const snapshot=approvalSnapshot(result),row={version:1,reference:sale.reference,amount:sale.amount,approvedAt:new Date().toISOString(),result:snapshot};
    posApprovalMemory.set(inflightKey,row);
    try{
      appendPosApproval(sale,snapshot,env);
      return{...snapshot,replayed:false,journal:"disk"};
    }catch(error){
      return{...snapshot,ok:false,approved:true,status:"approved_journal_error",error:"journal_write_failed",replayed:false,journal:"memory",
        message:`Terminal approved the payment but Cafino could not persist the approval journal. Do NOT restart or create a new payment; reconcile RRN ${snapshot.referenceNumber||snapshot.traceNumber||"(missing)"} and retry only after fixing local storage.`};
    }
  })().finally(()=>posApprovalInflight.delete(inflightKey));
  posApprovalInflight.set(inflightKey,task);
  return task;
}
async function sendPosAmount(input,env=process.env){
  const adapter=selected(env,"POS","MANUAL"),sale=saleInput(input,env);
  if(!sale)return{ok:false,approved:false,adapter,error:"invalid_amount",message:"POS amount must be a positive integer in the configured unit."};
  if(adapter==="MANUAL")return{ok:false,approved:false,requiresManual:true,adapter,amount:sale.amount,message:"Enter the amount on the POS terminal manually and confirm it in Cafino."};
  if(adapter==="VENDOR_SDK")return{ok:false,approved:false,adapter,status:"planned",amount:sale.amount,message:"Direct vendor SDK adapter needs the exact terminal/PSP SDK."};
  try{return await authorizeDirectPos(sale,adapter,env)}
  catch(error){return{ok:false,approved:false,adapter,status:"error",amount:sale.amount,message:safeText(error?.message||error,180)}}
}
module.exports={ADAPTERS,registryPayload,callPager,sendPosAmount,allowedBridgeHost,httpBridgeUrl,tcpBridgeConfig,saleInput,normalizeResponse,posJournalPath,ensurePosJournalReadable,appendPosApproval,cachedPosApproval};

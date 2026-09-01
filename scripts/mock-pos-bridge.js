const http=require("http");
const crypto=require("crypto");

const host="127.0.0.1";
const port=Number(process.env.CAF_INO_MOCK_POS_PORT||17890);
const mode=String(process.env.CAF_INO_MOCK_POS_MODE||"approve").toLowerCase();
const seen=new Map();

function json(res,status,payload){res.writeHead(status,{"content-type":"application/json; charset=utf-8","cache-control":"no-store"});res.end(JSON.stringify(payload))}
function readBody(req){return new Promise((resolve,reject)=>{let body="";req.on("data",chunk=>{body+=chunk;if(body.length>64*1024){reject(new Error("request_too_large"));req.destroy()}});req.on("end",()=>{try{resolve(JSON.parse(body||"{}"))}catch{reject(new Error("invalid_json"))}});req.on("error",reject)})}
function rrn(reference){return crypto.createHash("sha256").update(String(reference)).digest("hex").slice(0,12).toUpperCase()}

const server=http.createServer(async(req,res)=>{
  if(req.method==="GET"&&req.url==="/health")return json(res,200,{ok:true,service:"cafino-mock-pos",mode});
  if(req.method!=="POST"||req.url!=="/sale")return json(res,404,{success:false,status:"not_found"});
  try{
    const body=await readBody(req);const amount=Number(body.amount);const reference=String(body.reference||"").slice(0,80);
    if(!Number.isSafeInteger(amount)||amount<=0||!reference)return json(res,400,{success:false,status:"invalid_request",message:"amount and reference are required"});
    const previous=seen.get(reference);
    if(previous){if(previous.amount!==amount)return json(res,409,{success:false,status:"reference_conflict",message:"reference was already used with another amount"});return json(res,200,previous.response)}
    const approved=mode!=="decline";
    const response=approved?{success:true,status:"approved",rrn:rrn(reference),trace:rrn(`${reference}:trace`).slice(0,6),terminal_id:"MOCK-LOCAL",masked_pan:"****4242",message:"mock approved"}:{success:false,status:"declined",message:"mock declined"};
    seen.set(reference,{amount,response});return json(res,200,response);
  }catch(error){return json(res,400,{success:false,status:"bad_request",message:String(error?.message||error)})}
});
server.listen(port,host,()=>{
  console.log(`Cafino MOCK POS bridge listening on http://${host}:${port}/sale`);
  console.log(`Mode: ${mode}. This server is for development/testing only.`);
});

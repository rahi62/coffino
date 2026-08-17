const fs=require("fs");
const path=require("path");

function read(file){try{const data=JSON.parse(fs.readFileSync(file,"utf8"));return Array.isArray(data?.entries)?data:{entries:[]}}catch{return{entries:[]}}}
function write(file,data){fs.mkdirSync(path.dirname(file),{recursive:true});const tmp=`${file}.${process.pid}.tmp`;fs.writeFileSync(tmp,JSON.stringify(data,null,2),{encoding:"utf8",mode:0o600});fs.renameSync(tmp,file)}
function prune(entries,now=Date.now()){const cutoff=now-30*24*60*60*1000;return entries.filter(x=>Date.parse(x.updated_at||x.created_at||0)>=cutoff).slice(-500)}
function reusable(file,reference,amount){if(!reference)return null;const row=read(file).entries.find(x=>x.reference===reference&&x.amount===Number(amount)&&x.state==="approved");return row||null}
function recordApproved(file,{reference,amount,result}){if(!reference)throw new Error("POS journal reference is required");const data=read(file);const now=new Date().toISOString();const existing=data.entries.find(x=>x.reference===reference);if(existing){if(existing.amount!==Number(amount))throw new Error("POS journal reference was reused with another amount");existing.state="approved";existing.result=result;existing.updated_at=now}else data.entries.push({reference,amount:Number(amount),state:"approved",result,created_at:now,updated_at:now});data.entries=prune(data.entries);write(file,data);return data.entries.find(x=>x.reference===reference)}
function markCommitted(file,reference,orderNumber=""){const data=read(file);const row=data.entries.find(x=>x.reference===reference);if(!row)return{ok:false,reason:"not_found"};row.state="committed";row.order_number=String(orderNumber||"").slice(0,80);row.updated_at=new Date().toISOString();data.entries=prune(data.entries);write(file,data);return{ok:true,reference,state:row.state}}
function list(file){return prune(read(file).entries).slice().reverse()}
module.exports={read,reusable,recordApproved,markCommitted,list,prune};

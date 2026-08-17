const {NsisUpdater}=require("electron-updater");

function normalizeUpdateUrl(value){
  const raw=String(value||"").trim();
  if(!raw)return"";
  let url;try{url=new URL(raw)}catch{return""}
  if(url.protocol!=="https:")return"";
  return url.toString().replace(/\/$/,"");
}
function normalizeUpdateChannel(value){
  const channel=String(value||"").trim().toLowerCase();
  if(channel==="stable"||channel==="latest")return"latest";
  if(channel==="beta")return"beta";
  return"";
}
function inferUpdateChannel(url,explicit=""){
  const normalizedExplicit=normalizeUpdateChannel(explicit);
  if(normalizedExplicit)return normalizedExplicit;
  const normalizedUrl=normalizeUpdateUrl(url);
  if(!normalizedUrl)return"";
  try{
    const parts=new URL(normalizedUrl).pathname.split("/").filter(Boolean);
    return parts.at(-1)?.toLowerCase()==="beta"?"beta":"latest";
  }catch{return""}
}
function createUpdater({url,channel="",logger=null}={}){
  const normalized=normalizeUpdateUrl(url);
  const normalizedChannel=inferUpdateChannel(normalized,channel);
  if(!normalized||!normalizedChannel)return null;
  const updater=new NsisUpdater({provider:"generic",url:normalized,channel:normalizedChannel});
  updater.channel=normalizedChannel;
  updater.autoDownload=false;
  updater.autoInstallOnAppQuit=false;
  updater.allowDowngrade=false;
  if(logger)updater.logger=logger;
  return updater;
}
function updaterStatus(updater,extra={}){return{enabled:!!updater,...extra};}

module.exports={normalizeUpdateUrl,normalizeUpdateChannel,inferUpdateChannel,createUpdater,updaterStatus};

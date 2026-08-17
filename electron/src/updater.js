const {NsisUpdater}=require("electron-updater");

function normalizeUpdateUrl(value){
  const raw=String(value||"").trim();
  if(!raw)return"";
  let url;try{url=new URL(raw)}catch{return""}
  if(url.protocol!=="https:")return"";
  return url.toString().replace(/\/$/,"");
}
function normalizeUpdateChannel(value){
  const channel=String(value||"latest").trim().toLowerCase();
  if(channel==="stable"||channel==="latest")return"latest";
  if(channel==="beta")return"beta";
  return"";
}
function createUpdater({url,channel="latest",logger=null}={}){
  const normalized=normalizeUpdateUrl(url);
  const normalizedChannel=normalizeUpdateChannel(channel);
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

module.exports={normalizeUpdateUrl,normalizeUpdateChannel,createUpdater,updaterStatus};

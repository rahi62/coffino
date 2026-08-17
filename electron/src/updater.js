const {NsisUpdater}=require("electron-updater");

function normalizeUpdateUrl(value){
  const raw=String(value||"").trim();
  if(!raw)return"";
  let url;try{url=new URL(raw)}catch{return""}
  if(url.protocol!=="https:")return"";
  return url.toString().replace(/\/$/,"");
}
function createUpdater({url,logger=null}={}){
  const normalized=normalizeUpdateUrl(url);if(!normalized)return null;
  const updater=new NsisUpdater({provider:"generic",url:normalized});
  updater.autoDownload=false;
  updater.autoInstallOnAppQuit=false;
  updater.allowDowngrade=false;
  if(logger)updater.logger=logger;
  return updater;
}
function updaterStatus(updater,extra={}){return{enabled:!!updater,...extra};}

module.exports={normalizeUpdateUrl,createUpdater,updaterStatus};

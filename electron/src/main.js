const {app,BrowserWindow,ipcMain,dialog,shell}=require("electron");
const {spawn,spawnSync}=require("child_process");
const path=require("path"),fs=require("fs"),crypto=require("crypto");
let backend=null,frontend=null,notificationTimer=null,notificationWorkerBusy=false;

function dataDir(){const d=app.getPath("userData");fs.mkdirSync(d,{recursive:true});return d;}
function dbPath(){return path.join(dataDir(),"cafino.sqlite3")}
function devBackendDir(){return path.resolve(__dirname,"../../backend")}
function packagedBackend(){return path.join(process.resourcesPath,"backend",process.platform==="win32"?"cafino-backend.exe":"cafino-backend")}
function devPython(){const d=devBackendDir();return process.platform==="win32"?path.join(d,".venv","Scripts","python.exe"):path.join(d,".venv","bin","python")}
function backendEnv(){
  const secretFile=path.join(dataDir(),"secret.key");
  if(!fs.existsSync(secretFile))fs.writeFileSync(secretFile,crypto.randomBytes(48).toString("hex"),{mode:0o600});
  return {...process.env,DATABASE_URL:`sqlite:///${dbPath().replace(/\\/g,"/")}`,DJANGO_SECRET_KEY:fs.readFileSync(secretFile,"utf8"),DJANGO_DEBUG:"0",DJANGO_ALLOWED_HOSTS:"127.0.0.1,localhost",DJANGO_SECURE_SSL_REDIRECT:"0",CAF_INO_ENV:"local"};
}
function backendExec(args=[],opts={}){
  if(app.isPackaged){
    const exe=packagedBackend();if(!fs.existsSync(exe))return null;
    return opts.sync?spawnSync(exe,args,{env:backendEnv(),encoding:"utf8",windowsHide:true}):spawn(exe,args,{env:backendEnv(),stdio:opts.stdio||"ignore",windowsHide:true});
  }
  const py=devPython();if(!fs.existsSync(py))return null;
  const full=["manage.py",...args];return opts.sync?spawnSync(py,full,{cwd:devBackendDir(),env:{...process.env,DATABASE_URL:`sqlite:///${path.join(devBackendDir(),"db.sqlite3").replace(/\\/g,"/")}`},encoding:"utf8"}):spawn(py,full,{cwd:devBackendDir(),env:process.env,stdio:opts.stdio||"inherit"});
}
function startBackend(){
  if(process.env.CAFINO_SKIP_BACKEND==="1")return;
  if(app.isPackaged)backend=backendExec([],{stdio:"ignore"});
  else{const py=devPython();if(fs.existsSync(py))backend=spawn(py,["manage.py","runserver","127.0.0.1:8000","--noreload"],{cwd:devBackendDir(),stdio:"inherit"})}
}
function startFrontend(){
  if(!app.isPackaged)return;
  const server=path.join(process.resourcesPath,"frontend","server.js");if(!fs.existsSync(server))return;
  frontend=spawn(process.execPath,[server],{cwd:path.dirname(server),env:{...process.env,ELECTRON_RUN_AS_NODE:"1",PORT:"3000",HOSTNAME:"127.0.0.1",NEXT_PUBLIC_API_URL:"http://127.0.0.1:8000/api/v1",NEXT_PUBLIC_API_ROOT:"http://127.0.0.1:8000"},stdio:"ignore"});
}
function processNotificationQueue(){
  if(notificationWorkerBusy)return;notificationWorkerBusy=true;
  let p;
  if(app.isPackaged)p=backendExec(["--process-notifications"]);
  else{const py=devPython();if(!fs.existsSync(py)){notificationWorkerBusy=false;return};p=spawn(py,["manage.py","process_notifications"],{cwd:devBackendDir(),stdio:"ignore"})}
  if(!p){notificationWorkerBusy=false;return}p.on("exit",()=>notificationWorkerBusy=false);p.on("error",()=>notificationWorkerBusy=false);
}
function startNotificationWorker(){setTimeout(processNotificationQueue,15000);notificationTimer=setInterval(processNotificationQueue,60000)}
async function waitForUrl(url,attempts=60,delay=500){
  for(let i=0;i<attempts;i++){try{const r=await fetch(url);if(r.ok||r.status<500)return true}catch{}await new Promise(r=>setTimeout(r,delay))}
  return false;
}
async function createWindow(){
  const target=process.env.CAFINO_FRONTEND_URL||"http://127.0.0.1:3000";
  await waitForUrl(target,80,500);
  const win=new BrowserWindow({width:1440,height:900,minWidth:1100,minHeight:700,webPreferences:{preload:path.join(__dirname,"preload.js"),contextIsolation:true,nodeIntegration:false,sandbox:true}});
  await win.loadURL(target);
}

function backup(target){
  if(app.isPackaged){const r=backendExec(["--backup",target],{sync:true});return r&&r.status===0?{ok:true}:{ok:false,error:r?.stderr||"Backup failed"}}
  const py=devPython(),src=path.join(devBackendDir(),"db.sqlite3");if(!fs.existsSync(py)||!fs.existsSync(src))return{ok:false,error:"Local database/runtime missing"};
  const code='import sqlite3,sys; s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()';const r=spawnSync(py,["-c",code,src,target],{encoding:"utf8"});return r.status===0?{ok:true}:{ok:false,error:r.stderr};
}
function restore(source){
  const emergency=path.join(dataDir(),`before-restore-${Date.now()}.sqlite3`);
  if(app.isPackaged){
    if(fs.existsSync(dbPath())){const b=backup(emergency);if(!b.ok)return b}
    if(backend){backend.kill();backend=null}
    const r=backendExec(["--restore",source],{sync:true});if(!r||r.status!==0)return{ok:false,error:r?.stderr||"Restore failed"};
    startBackend();return{ok:true,emergency};
  }
  return{ok:false,error:"Restore in development: replace backend/db.sqlite3 manually after stopping Django."};
}

function esc(v){return String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
function receiptHtml(p){
  const template=p.template||{};
  const paperWidth=Number(p.paper_width)===58?58:80;
  const templateHeader=template.header?`<div class="center muted">${esc(template.header).replace(/\n/g,"<br>")}</div>`:"";
  const templateFooter=template.footer?`<p class="center muted">${esc(template.footer).replace(/\n/g,"<br>")}</p>`:"";
  const customer=template.show_customer!==false&&p.customer?`<div class="muted">مشتری: ${esc(p.customer.name||"")}${p.customer.phone?` — ${esc(p.customer.phone)}`:""}</div>`:"";
  const items=(p.items||[]).map(x=>`<tr><td>${esc(x.name)}</td><td>${esc(x.quantity)}</td><td>${Number(x.line_total||0).toLocaleString()}</td></tr>`).join("");
  const pays=(p.payments||[]).map(x=>`<div>${x.payer_label?esc(x.payer_label)+" — ":""}${esc(x.method)}: ${Number(x.amount||0).toLocaleString()}${Number(x.change||0)>0?` | باقی‌مانده ${Number(x.change).toLocaleString()}`:""}</div>`).join("");
  return `<!doctype html><html dir="rtl"><head><meta charset="utf-8"><style>
  @page{size:${paperWidth}mm auto;margin:3mm}body{font-family:Tahoma,Arial,sans-serif;font-size:11px;color:#000;margin:0}h2{text-align:center;margin:4px 0}
  .center{text-align:center}.row{display:flex;justify-content:space-between;border-top:1px dashed #777;padding:4px 0}
  table{width:100%;border-collapse:collapse}th,td{padding:3px;text-align:right;border-bottom:1px dashed #aaa}
  .total{font-size:14px;font-weight:bold}.muted{font-size:9px}
  </style></head><body>${templateHeader}<h2>${esc(p.business)}</h2><div class="center">${esc(p.branch)}</div>
  <div class="row"><span>سفارش #${esc(p.order_number)}</span><span>${esc(p.order_type)}</span></div>
  ${p.table?`<div>میز: ${esc(p.table)}</div>`:""}${customer}<table><thead><tr><th>شرح</th><th>تعداد</th><th>مبلغ</th></tr></thead><tbody>${items}</tbody></table>
  <div class="row"><span>جمع</span><span>${Number(p.subtotal||0).toLocaleString()}</span></div>
  ${Number(p.discount_total||0)>0?`<div class="row"><span>تخفیف</span><span>-${Number(p.discount_total).toLocaleString()}</span></div>`:""}
  ${template.show_service_charge!==false&&Number(p.service_charge_total||0)>0?`<div class="row"><span>${esc(p.service_label||"حق سرویس")}</span><span>${Number(p.service_charge_total).toLocaleString()}</span></div>`:""}
  ${Number(p.delivery_fee_total||0)>0?`<div class="row"><span>هزینه ارسال</span><span>${Number(p.delivery_fee_total).toLocaleString()}</span></div>`:""}
  ${template.show_tax!==false&&Number(p.tax_total||0)>0?`<div class="row"><span>${esc(p.tax_label||"مالیات")}</span><span>${Number(p.tax_total).toLocaleString()}</span></div>`:""}
  <div class="row total"><span>قابل پرداخت</span><span>${Number(p.grand_total||0).toLocaleString()}</span></div>
  <div>${pays}</div>${templateFooter}<p class="center muted">کافینو</p></body></html>`;
}
function kitchenHtml(p){
 const template=p.template||{};
 const templateHeader=template.header?`<div class="center">${esc(template.header).replace(/\n/g,"<br>")}</div>`:"";
 const templateFooter=template.footer?`<p class="center">${esc(template.footer).replace(/\n/g,"<br>")}</p>`:"";
 const items=(p.items||[]).map(x=>`<div class="item"><b>${esc(x.quantity)} × ${esc(x.name)}</b>${x.notes?`<div>${esc(x.notes)}</div>`:""}</div>`).join("");
 return `<!doctype html><html dir="rtl"><head><meta charset="utf-8"><style>@page{margin:3mm}body{font-family:Tahoma,Arial,sans-serif;font-size:14px}.head{text-align:center;font-size:20px;font-weight:bold}.center{text-align:center;font-size:11px}.item{border-top:1px dashed #000;padding:7px 0}</style></head><body>${templateHeader}<div class="head">#${esc(p.order_number)} — ${esc(p.station)}</div>${p.table?`<div>میز ${esc(p.table)}</div>`:""}<div>${esc(p.order_type)}</div>${items}${templateFooter}</body></html>`;
}
function savedLayout(template,type){
  const defaults=type==="RECEIPT"?["business","header","order","customer","items","summary","payment","barcode","footer"]:["business","header","order","items","footer"];
  const stored=template&&template.layout||{};
  const allowed=new Set(defaults);
  const blocks=Array.isArray(stored.blocks)?stored.blocks.filter(block=>allowed.has(block)):defaults;
  return {paperWidth:Number(stored.paper_width)===58?58:80,blocks:blocks.length?blocks:defaults};
}
function faMoney(value){return Number(value||0).toLocaleString("fa-IR");}
function savedReceiptHtml(p){
  const template=p.template||{},layout=savedLayout(template,"RECEIPT");
  const header=template.header?'<div class="center muted">'+esc(template.header).replace(/\n/g,"<br>")+"</div>":"";
  const footer=template.footer?'<p class="center muted">'+esc(template.footer).replace(/\n/g,"<br>")+"</p>":"";
  const customer=template.show_customer!==false&&p.customer?'<div class="muted">مشتری: '+esc(p.customer.name||"")+(p.customer.phone?" — "+esc(p.customer.phone):"")+"</div>":"";
  const items=(p.items||[]).map(x=>"<tr><td>"+esc(x.name)+"</td><td>"+esc(x.quantity)+"</td><td>"+faMoney(x.line_total)+"</td></tr>").join("");
  const payments=(p.payments||[]).map(x=>"<div>"+(x.payer_label?esc(x.payer_label)+" — ":"")+esc(x.method)+": "+faMoney(x.amount)+(Number(x.change||0)>0?" | باقی‌مانده "+faMoney(x.change):"")+"</div>").join("");
  const summary='<div class="row"><span>جمع</span><span>'+faMoney(p.subtotal)+"</span></div>"+
    (Number(p.discount_total||0)>0?'<div class="row"><span>تخفیف</span><span>-'+faMoney(p.discount_total)+"</span></div>":"")+
    (template.show_service_charge!==false&&Number(p.service_charge_total||0)>0?'<div class="row"><span>'+esc(p.service_label||"حق سرویس")+"</span><span>"+faMoney(p.service_charge_total)+"</span></div>":"")+
    (Number(p.delivery_fee_total||0)>0?'<div class="row"><span>هزینه ارسال</span><span>'+faMoney(p.delivery_fee_total)+"</span></div>":"")+
    (template.show_tax!==false&&Number(p.tax_total||0)>0?'<div class="row"><span>'+esc(p.tax_label||"مالیات")+"</span><span>"+faMoney(p.tax_total)+"</span></div>":"")+
    '<div class="row total"><span>قابل پرداخت</span><span>'+faMoney(p.grand_total)+"</span></div>";
  const parts={
    business:"<h2>"+esc(p.business)+"</h2><div class=\"center\">"+esc(p.branch)+"</div>",
    header,
    order:'<div class="row"><span>سفارش #'+esc(p.order_number)+"</span><span>"+esc(p.order_type)+"</span></div>"+(p.table?"<div>میز: "+esc(p.table)+"</div>":""),
    customer,
    items:'<table><thead><tr><th>شرح</th><th>تعداد</th><th>مبلغ</th></tr></thead><tbody>'+items+"</tbody></table>",
    summary,
    payment:payments?'<div class="row"><div>'+payments+"</div></div>":"",
    barcode:'<div class="barcode">'+esc(p.order_number)+"</div>",
    footer,
  };
  const body=layout.blocks.map(block=>parts[block]||"").join("");
  return '<!doctype html><html dir="rtl"><head><meta charset="utf-8"><style>@page{size:'+layout.paperWidth+'mm auto;margin:3mm}body{font-family:Tahoma,Arial,sans-serif;font-size:11px;color:#000;margin:0}h2{text-align:center;margin:4px 0}.center{text-align:center}.row{display:flex;justify-content:space-between;border-top:1px dashed #777;padding:4px 0}table{width:100%;border-collapse:collapse}th,td{padding:3px;text-align:right;border-bottom:1px dashed #aaa}.total{font-size:14px;font-weight:bold}.muted{font-size:9px}.barcode{direction:ltr;letter-spacing:3px;text-align:center;font-family:monospace;margin:8px 0}</style></head><body>'+body+"</body></html>";
}
function savedKitchenHtml(p){
  const template=p.template||{},layout=savedLayout(template,"KITCHEN");
  const header=template.header?'<div class="center">'+esc(template.header).replace(/\n/g,"<br>")+"</div>":"";
  const footer=template.footer?'<p class="center">'+esc(template.footer).replace(/\n/g,"<br>")+"</p>":"";
  const items=(p.items||[]).map(x=>'<div class="item"><b>'+esc(x.quantity)+" × "+esc(x.name)+"</b>"+(x.notes?"<div>"+esc(x.notes)+"</div>":"")+"</div>").join("");
  const parts={
    business:'<div class="head">'+esc(p.station)+"</div>",
    header,
    order:'<div class="head">#'+esc(p.order_number)+"</div>"+(p.table?"<div>میز "+esc(p.table)+"</div>":"")+"<div>"+esc(p.order_type)+"</div>",
    items,
    footer,
  };
  const body=layout.blocks.map(block=>parts[block]||"").join("");
  return '<!doctype html><html dir="rtl"><head><meta charset="utf-8"><style>@page{size:'+layout.paperWidth+'mm auto;margin:3mm}body{font-family:Tahoma,Arial,sans-serif;font-size:14px}.head{text-align:center;font-size:20px;font-weight:bold}.center{text-align:center;font-size:11px}.item{border-top:1px dashed #000;padding:7px 0}</style></head><body>'+body+"</body></html>";
}
async function printHtml(html,deviceName){
  const win=new BrowserWindow({show:false,webPreferences:{contextIsolation:true,nodeIntegration:false,sandbox:true}});
  try{
    await win.loadURL("data:text/html;charset=utf-8,"+encodeURIComponent(html));
    return await new Promise(resolve=>{
      win.webContents.print({silent:true,printBackground:true,deviceName:deviceName||undefined,margins:{marginType:"none"}},(success,failureReason)=>{
        if(!win.isDestroyed())win.destroy();
        resolve(success?{ok:true}:{ok:false,error:failureReason||"Print failed"});
      });
    });
  }catch(e){if(!win.isDestroyed())win.destroy();return{ok:false,error:String(e)}}
}



app.whenReady().then(()=>{startBackend();startFrontend();startNotificationWorker();createWindow();app.on("activate",()=>{if(BrowserWindow.getAllWindows().length===0)createWindow()})});
app.on("window-all-closed",()=>{if(process.platform!=="darwin")app.quit()});
app.on("before-quit",()=>{if(notificationTimer)clearInterval(notificationTimer);if(backend)backend.kill();if(frontend)frontend.kill()});

ipcMain.handle("system:health",async()=>({ok:true,packaged:app.isPackaged,platform:process.platform,version:app.getVersion(),dbPath:app.isPackaged?dbPath():path.join(devBackendDir(),"db.sqlite3")}));
ipcMain.handle("backup:create",async()=>{const r=await dialog.showSaveDialog({title:"ذخیره بکاپ Cafino",defaultPath:`cafino-backup-${new Date().toISOString().slice(0,10)}.sqlite3`});if(r.canceled||!r.filePath)return{ok:false,canceled:true};return{...backup(r.filePath),path:r.filePath}});
ipcMain.handle("backup:restore",async()=>{const r=await dialog.showOpenDialog({title:"انتخاب بکاپ Cafino",properties:["openFile"]});if(r.canceled||!r.filePaths[0])return{ok:false,canceled:true};return restore(r.filePaths[0])});
ipcMain.handle("system:openExternal",async(_,url)=>{if(/^https?:\/\//.test(url))await shell.openExternal(url);return true});
ipcMain.handle("printer:list",async()=>{const w=BrowserWindow.getAllWindows()[0];return w?await w.webContents.getPrintersAsync():[]});
ipcMain.handle("printer:printHtml",async(_,args)=>printHtml(args?.html||"",args?.deviceName));
ipcMain.handle("printer:printReceipt",async(_,args)=>printHtml(savedReceiptHtml(args?.payload||{}),args?.deviceName));
ipcMain.handle("printer:printKitchen",async(_,args)=>printHtml(savedKitchenHtml(args?.payload||{}),args?.deviceName));
ipcMain.handle("pager:call",async(_,pager)=>({ok:false,message:"Pager adapter requires selected hardware protocol.",pager}));
ipcMain.handle("pos:sendAmount",async(_,amount)=>({ok:false,message:"Bank POS requires selected vendor SDK/API.",amount}));

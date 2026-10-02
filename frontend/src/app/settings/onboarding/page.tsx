"use client";

import Link from "next/link";
import {useEffect,useMemo,useState} from "react";
import {CheckCircle2,CircleAlert,Globe2,MessageSquare,ReceiptText,Settings2,Store} from "lucide-react";

import {SettingsReadiness,useSettings} from "@/components/settings/settings-context";
import {api} from "@/lib/api";

type Preset={key:string;label:string;business_type:string;description:string;modules:string[];stations:string[]};
type BootstrapResult={register:boolean;hall:boolean;tables:number;stations:number;online_settings:boolean};
type ApplyResult={
  preset:string;
  business:{id:number;name:string;business_type:string;deployment_type:string};
  branch:{id:number;name:string;address:string;phone:string};
  enabled_modules:string[];
  created:BootstrapResult;
  readiness:SettingsReadiness;
};
type HealthCheck={key:string;title:string;status:"ok"|"warning"|"error"|"skipped";message:string;mode:string;details:Record<string,unknown>};
type HealthResult={branch:{id:number;name:string};live:boolean;summary:{ok:number;warning:number;error:number;total:number};checks:HealthCheck[]};
type PrinterHealth={branch:{id:number;name:string};check:HealthCheck};

type FormState={
  branch:string;branch_name:string;branch_phone:string;branch_address:string;deployment_type:string;
  replace_modules:boolean;create_register:boolean;register_name:string;
  hall_name:string;table_count:string;table_capacity:string;create_stations:boolean;create_online_settings:boolean;
};

const moduleLabels:Record<string,string>={
 POS:"فروش / POS",DINE_IN:"سالن",TAKEAWAY:"بیرون‌بر",KITCHEN_DISPLAY:"KDS",INVENTORY:"انبار",RECIPES:"رسپی",
 PRODUCTION:"تولید",PURCHASING:"خرید",ACCOUNTING:"مالی مدیریتی",CUSTOMERS:"مشتریان",LOYALTY:"وفاداری",REPORTING:"گزارش‌ها",
 PRINTING:"چاپ",RESERVATION:"رزرو",MULTI_BRANCH:"چندشعبه",ONLINE_ORDERING:"سفارش آنلاین",DELIVERY:"ارسال",
 PAYMENT_GATEWAY:"درگاه پرداخت",NOTIFICATIONS:"اعلان‌ها",SMS:"پیامک"
};

const deploymentLabels:Record<string,string>={LOCAL:"Local / ویندوز",SAAS:"Cloud SaaS",DEDICATED:"Dedicated Managed"};

export default function OnboardingPage(){
 const {data,selectedBranchId,setSelectedBranchId,refresh}=useSettings();
 const [presets,setPresets]=useState<Preset[]>([]);
 const [presetKey,setPresetKey]=useState("");
 const [step,setStep]=useState(1);
 const [busy,setBusy]=useState(false);
 const [message,setMessage]=useState("");
 const [result,setResult]=useState<ApplyResult|null>(null);
 const [health,setHealth]=useState<HealthResult|null>(null);
 const [printerHealth,setPrinterHealth]=useState<HealthCheck|null>(null);
 const [form,setForm]=useState<FormState>({
   branch:"",branch_name:"",branch_phone:"",branch_address:"",deployment_type:"LOCAL",
   replace_modules:true,create_register:true,register_name:"صندوق اصلی",hall_name:"سالن اصلی",table_count:"0",table_capacity:"4",
   create_stations:true,create_online_settings:true,
 });

 useEffect(()=>{api<{presets:Preset[]}>("/settings/onboarding/presets/").then(x=>setPresets(x.presets)).catch(e=>setMessage(e.message))},[]);
 useEffect(()=>{
   if(!data)return;
   setForm(x=>({...x,deployment_type:data.business.deployment_type||"LOCAL"}));
 },[data?.business.deployment_type]);
 useEffect(()=>{
   if(!data)return;
   const branch=data.branches.find(x=>x.id===selectedBranchId)||data.branches[0];
   if(branch)setForm(x=>({...x,branch:String(branch.id),branch_name:branch.name,branch_phone:branch.phone||"",branch_address:branch.address||""}));
 },[data,selectedBranchId]);
 useEffect(()=>{
   if(presetKey||!presets.length||!data)return;
   const found=presets.find(x=>x.business_type===data.business.business_type)||presets[0];
   setPresetKey(found.key);
 },[presets,data,presetKey]);

 const preset=useMemo(()=>presets.find(x=>x.key===presetKey)||null,[presets,presetKey]);
 const has=(key:string)=>!!preset?.modules.includes(key);
 const choosePreset=(key:string)=>{
   const p=presets.find(x=>x.key===key);setPresetKey(key);setMessage("");
   setForm(x=>({...x,table_count:p?.modules.includes("DINE_IN")?(x.table_count==="0"?"10":x.table_count):"0"}));
 };
 const chooseBranch=(value:string)=>{
   if(!data)return;
   if(!value){setForm(x=>({...x,branch:"",branch_name:"شعبه اصلی",branch_phone:"",branch_address:""}));return}
   const branch=data.branches.find(x=>x.id===Number(value));
   if(branch)setForm(x=>({...x,branch:value,branch_name:branch.name,branch_phone:branch.phone||"",branch_address:branch.address||""}));
 };

 const apply=async()=>{
   if(!preset){setMessage("نوع کسب‌وکار را انتخاب کنید.");return}
   if(!form.branch_name.trim()){setMessage("نام شعبه لازم است.");return}
   setBusy(true);setMessage("");setHealth(null);setPrinterHealth(null);
   try{
     const response=await api<ApplyResult>("/settings/onboarding/apply/",{method:"POST",body:JSON.stringify({
       preset:preset.key,branch:form.branch?Number(form.branch):null,deployment_type:form.deployment_type,
       branch_name:form.branch_name,branch_phone:form.branch_phone,branch_address:form.branch_address,
       replace_modules:form.replace_modules,create_register:form.create_register,register_name:form.register_name,
       hall_name:form.hall_name,table_count:Number(form.table_count||0),table_capacity:Number(form.table_capacity||4),
       create_stations:form.create_stations,create_online_settings:form.create_online_settings,
     })});
     setResult(response);setSelectedBranchId(response.branch.id);setStep(4);await refresh();
     await runHealth(false,response.branch.id);
   }catch(e:any){setMessage(e.message||"راه‌اندازی انجام نشد")}
   finally{setBusy(false)}
 };

 const runHealth=async(live:boolean,branchId?:number)=>{
   const id=branchId||result?.branch.id||selectedBranchId;if(!id)return;
   setBusy(true);setMessage("");
   try{setHealth(await api<HealthResult>(`/settings/health/?branch=${id}&live=${live?1:0}`))}
   catch(e:any){setMessage(e.message||"Health Check انجام نشد")}
   finally{setBusy(false)}
 };

 const runPrinterHealth=async()=>{
   const branchId=result?.branch.id||selectedBranchId;if(!branchId)return;
   setMessage("");
   const bridge=(window as unknown as {cafino?:{listPrinters?:()=>Promise<Array<{name?:string;displayName?:string}>>}}).cafino;
   if(!bridge?.listPrinters){
     setPrinterHealth({key:"printer_runtime",title:"پرینتر محلی",status:"warning",message:"این تست فقط داخل Cafino Desktop/Electron قابل اجرا است. در نسخه وب، پیکربندی PrinterDevice را بررسی کنید.",mode:"hardware-runtime",details:{}});
     return;
   }
   setBusy(true);
   try{
     const devices=(await bridge.listPrinters()).map(x=>String(x.name||x.displayName||"").trim()).filter(Boolean);
     const response=await api<PrinterHealth>("/settings/health/printer/",{method:"POST",body:JSON.stringify({branch:branchId,devices})});
     setPrinterHealth(response.check);
   }catch(e:any){setMessage(e.message||"تست پرینتر انجام نشد")}
   finally{setBusy(false)}
 };

 if(!data)return null;
 return <div>
   <div className="mb-5 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
     <div><h2 className="text-3xl font-black">راه‌اندازی هوشمند Cafino</h2><p className="text-[#8d8178] mt-1">Preset مناسب را انتخاب کن؛ Cafino فقط تنظیمات امن و قابل بازگشت را Bootstrap می‌کند و داده واقعی منو/انبار را جعل نمی‌کند.</p></div>
     <Link href="/settings" className="btn">بازگشت به مرکز تنظیمات</Link>
   </div>

   <div className="grid grid-cols-4 gap-2 mb-5">{["نوع کسب‌وکار","شعبه و استقرار","Bootstrap","تست و تکمیل"].map((label,index)=>{const n=index+1;const active=step===n;const done=step>n;return <button key={label} onClick={()=>n<step&&setStep(n)} className={`rounded-xl border p-3 text-right ${active?"bg-[#211711] text-white":done?"bg-emerald-50 border-emerald-200":"bg-white"}`}><span className="text-xs opacity-70">مرحله {n}</span><b className="block text-sm mt-1">{label}</b></button>})}</div>

   {message&&<div className="card p-3 mb-4 border-amber-200">{message}</div>}

   {step===1&&<section className="card p-5">
     <div className="flex items-center gap-2 mb-1"><Settings2 size={20}/><h3 className="font-black text-lg">Preset عملیاتی</h3></div><p className="text-sm text-[#8d8178] mb-4">Preset فقط ماژول‌ها و Defaultهای امن را تعیین می‌کند؛ هر قابلیت بعداً مستقل قابل تغییر است.</p>
     <div className="grid md:grid-cols-2 2xl:grid-cols-3 gap-3">{presets.map(p=><button key={p.key} onClick={()=>choosePreset(p.key)} className={`text-right border rounded-xl p-4 ${presetKey===p.key?"border-[#211711] ring-2 ring-[#211711]/10":"border-[#eadfd3]"}`}><div className="flex justify-between gap-2"><b className="text-lg">{p.label}</b>{presetKey===p.key&&<CheckCircle2 size={19} className="text-emerald-600"/>}</div><p className="text-sm text-[#8d8178] leading-6 mt-2">{p.description}</p><div className="flex flex-wrap gap-1 mt-3">{p.modules.slice(0,6).map(m=><span className="badge" key={m}>{moduleLabels[m]||m}</span>)}{p.modules.length>6&&<span className="badge">+{p.modules.length-6}</span>}</div></button>)}</div>
     <div className="flex justify-end mt-5"><button className="btn btn-primary" disabled={!preset} onClick={()=>setStep(2)}>مرحله بعد</button></div>
   </section>}

   {step===2&&<section className="card p-5">
     <div className="flex items-center gap-2"><Store size={20}/><h3 className="font-black text-lg">شعبه و مدل استقرار</h3></div><div className="grid lg:grid-cols-2 gap-4 mt-4">
       <label className="text-sm">مدل استقرار<select className="border rounded-xl p-2 w-full mt-1" value={form.deployment_type} onChange={e=>setForm({...form,deployment_type:e.target.value})}>{Object.entries(deploymentLabels).map(([key,label])=><option value={key} key={key}>{label}</option>)}</select></label>
       <label className="text-sm">شعبه هدف<select className="border rounded-xl p-2 w-full mt-1" value={form.branch} onChange={e=>chooseBranch(e.target.value)}><option value="">+ ساخت شعبه جدید</option>{data.branches.map(b=><option key={b.id} value={b.id}>{b.name}</option>)}</select></label>
       <label className="text-sm">نام شعبه<input className="border rounded-xl p-2 w-full mt-1" value={form.branch_name} onChange={e=>setForm({...form,branch_name:e.target.value})}/></label>
       <label className="text-sm">تلفن<input className="border rounded-xl p-2 w-full mt-1" value={form.branch_phone} onChange={e=>setForm({...form,branch_phone:e.target.value})}/></label>
       <label className="text-sm lg:col-span-2">آدرس<textarea className="border rounded-xl p-2 w-full mt-1" value={form.branch_address} onChange={e=>setForm({...form,branch_address:e.target.value})}/></label>
     </div>
     <div className="flex justify-between mt-5"><button className="btn" onClick={()=>setStep(1)}>قبلی</button><button className="btn btn-primary" onClick={()=>setStep(3)}>مرحله بعد</button></div>
   </section>}

   {step===3&&preset&&<section className="space-y-5">
     <div className="card p-5"><h3 className="font-black text-lg">ماژول‌های Preset «{preset.label}»</h3><div className="flex flex-wrap gap-2 mt-3">{preset.modules.map(m=><span key={m} className="badge">{moduleLabels[m]||m}</span>)}</div><label className="mt-4 border rounded-xl p-3 flex gap-2 items-start"><input type="checkbox" checked={form.replace_modules} onChange={e=>setForm({...form,replace_modules:e.target.checked})}/><span><b className="text-sm">Preset جایگزین انتخاب ماژول‌های فعلی شود</b><span className="block text-xs text-[#8d8178] mt-1">خاموش‌شدن ماژول داده‌های آن را حذف نمی‌کند. اگر این گزینه خاموش باشد فقط ماژول‌های Preset به تنظیمات فعلی اضافه می‌شوند.</span></span></label></div>
     <div className="grid xl:grid-cols-2 gap-5">
       {has("POS")&&<div className="card p-5"><h3 className="font-black">Default صندوق</h3><label className="flex gap-2 mt-3"><input type="checkbox" checked={form.create_register} onChange={e=>setForm({...form,create_register:e.target.checked})}/> اگر صندوق فعال وجود ندارد، یکی بساز</label>{form.create_register&&<input className="border rounded-xl p-2 w-full mt-3" value={form.register_name} onChange={e=>setForm({...form,register_name:e.target.value})}/>}</div>}
       {has("DINE_IN")&&<div className="card p-5"><h3 className="font-black">سالن و میز اولیه</h3><div className="grid grid-cols-3 gap-2 mt-3"><input className="border rounded-xl p-2 col-span-3" value={form.hall_name} onChange={e=>setForm({...form,hall_name:e.target.value})} placeholder="نام سالن"/><label className="text-xs">تعداد میز<input type="number" min="0" max="200" className="border rounded-xl p-2 w-full mt-1" value={form.table_count} onChange={e=>setForm({...form,table_count:e.target.value})}/></label><label className="text-xs">ظرفیت<input type="number" min="1" max="30" className="border rounded-xl p-2 w-full mt-1" value={form.table_capacity} onChange={e=>setForm({...form,table_capacity:e.target.value})}/></label></div></div>}
       {has("KITCHEN_DISPLAY")&&<div className="card p-5"><h3 className="font-black">ایستگاه‌های آماده‌سازی</h3><label className="flex gap-2 mt-3"><input type="checkbox" checked={form.create_stations} onChange={e=>setForm({...form,create_stations:e.target.checked})}/> ایستگاه‌های پیشنهادی Preset ساخته شوند</label><div className="flex flex-wrap gap-1 mt-3">{preset.stations.map(x=><span className="badge" key={x}>{x}</span>)}</div></div>}
       {has("ONLINE_ORDERING")&&<div className="card p-5"><h3 className="font-black">منوی آنلاین</h3><label className="flex gap-2 mt-3"><input type="checkbox" checked={form.create_online_settings} onChange={e=>setForm({...form,create_online_settings:e.target.checked})}/> تنظیمات اولیه Slug/QR ساخته شود</label><p className="text-xs text-[#8d8178] mt-2">پذیرش سفارش عمداً خودکار روشن نمی‌شود؛ بعد از تکمیل منو و Health Check آن را فعال کن.</p></div>}
     </div>
     <div className="card p-4 flex items-start gap-2"><CircleAlert size={18} className="text-amber-600 shrink-0"/><p className="text-sm leading-6">Cafino در Wizard محصول، قیمت، موجودی یا رسپی ساختگی ایجاد نمی‌کند. این داده‌ها باید واقعی باشند و Readiness بعد از Apply موارد باقی‌مانده را نشان می‌دهد.</p></div>
     <div className="flex justify-between"><button className="btn" onClick={()=>setStep(2)}>قبلی</button><button className="btn btn-primary" disabled={busy} onClick={apply}>{busy?"در حال اعمال…":"اعمال Preset و راه‌اندازی"}</button></div>
   </section>}

   {step===4&&<section className="space-y-5">
     <div className="card p-5"><div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between"><div><div className="flex gap-2 items-center"><CheckCircle2 className="text-emerald-600"/><h3 className="font-black text-lg">Bootstrap انجام شد</h3></div><p className="text-sm text-[#8d8178] mt-1">{result?`${result.business.name} — ${result.branch.name}`:"برای شعبه انتخابی می‌توانی Health Check را اجرا کنی."}</p></div>{result&&<div className="text-left"><b className="text-3xl">{result.readiness.overall.score}%</b><div className="text-xs text-[#8d8178]">Setup Readiness</div></div>}</div>
       {result&&<div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-2 mt-4"><SmallMetric label="صندوق" value={result.created.register?"ساخته شد":"موجود/رد شد"}/><SmallMetric label="میز جدید" value={String(result.created.tables)}/><SmallMetric label="Station جدید" value={String(result.created.stations)}/><SmallMetric label="Online Config" value={result.created.online_settings?"ساخته شد":"موجود/رد شد"}/><SmallMetric label="Blocker" value={String(result.readiness.overall.blocking)}/></div>}
     </div>

     <div className="card p-5"><div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between"><div><h3 className="font-black text-lg">Health Check اتصال‌ها</h3><p className="text-sm text-[#8d8178] mt-1">Config Check هیچ پیام یا پرداختی ایجاد نمی‌کند؛ Live Check فقط HEAD امن برای سنجش Reachability می‌فرستد.</p></div><div className="flex flex-wrap gap-2"><button className="btn" disabled={busy} onClick={()=>runHealth(false)}>Config Check</button><button className="btn btn-primary" disabled={busy} onClick={()=>runHealth(true)}>Live Network Check</button><button className="btn" disabled={busy} onClick={runPrinterHealth}>Local Printer Check</button></div></div>
       {health&&<><div className="grid grid-cols-3 gap-2 mt-4"><SmallMetric label="سالم" value={String(health.summary.ok)}/><SmallMetric label="هشدار" value={String(health.summary.warning)}/><SmallMetric label="خطا" value={String(health.summary.error)}/></div><div className="space-y-2 mt-4">{health.checks.map(x=><HealthRow key={x.key} check={x}/>)}{printerHealth&&<HealthRow check={printerHealth}/>}</div></>}
       {!health&&<div className="border rounded-xl p-4 text-sm text-[#8d8178] mt-4">هنوز Health Check اجرا نشده است.</div>}
     </div>

     <div className="grid md:grid-cols-3 gap-4"><ActionCard icon={<Globe2 size={19}/>} title="سفارش آنلاین" href="/settings/online" text="منو، Delivery Zone و درگاه را تکمیل کن."/><ActionCard icon={<MessageSquare size={19}/>} title="اعلان‌ها" href="/settings/notifications" text="SMS و Push Provider را تنظیم و بررسی کن."/><ActionCard icon={<ReceiptText size={19}/>} title="چاپ" href="/printing" text="System Name و قالب رسید/آشپزخانه را نهایی کن."/></div>
     <div className="flex justify-between"><button className="btn" onClick={()=>setStep(3)}>بازگشت به تنظیمات Wizard</button><Link className="btn btn-primary" href="/settings">مشاهده Checklist کامل</Link></div>
   </section>}
 </div>
}

function SmallMetric({label,value}:{label:string;value:string}){return <div className="rounded-xl bg-[#eee6dc] p-3"><span className="text-xs text-[#8d8178]">{label}</span><b className="block mt-1">{value}</b></div>}

function HealthRow({check}:{check:HealthCheck}){
 const icon=check.status==="ok"?<CheckCircle2 size={19} className="text-emerald-600"/>:<CircleAlert size={19} className={check.status==="error"?"text-red-600":"text-amber-600"}/>;
 const label=check.status==="ok"?"سالم":check.status==="error"?"خطا":check.status==="skipped"?"غیرفعال":"نیازمند بررسی";
 return <div className="border rounded-xl p-3 flex items-start gap-3"><div className="mt-0.5">{icon}</div><div className="flex-1 min-w-0"><div className="flex flex-wrap items-center gap-2"><b className="text-sm">{check.title}</b><span className="badge">{label}</span><span className="text-[10px] text-[#8d8178]">{check.mode}</span></div><p className="text-xs text-[#8d8178] leading-6 mt-1">{check.message}</p></div></div>
}

function ActionCard({icon,title,href,text}:{icon:React.ReactNode;title:string;href:string;text:string}){return <Link href={href} className="card p-4 hover:-translate-y-0.5 transition-transform"><div className="flex gap-2 items-center">{icon}<b>{title}</b></div><p className="text-xs text-[#8d8178] mt-2 leading-6">{text}</p></Link>}

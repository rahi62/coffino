"use client";

import {useEffect,useMemo,useState} from "react";
import {AlertTriangle,CheckCircle2,Database,HardDrive,RefreshCw,ServerCog,ShieldCheck,Usb,Workflow} from "lucide-react";

import {api} from "@/lib/api";

type Check={key:string;title:string;status:"ok"|"warning"|"error";detail:string;category:string;blocking:boolean;branch?:number;branch_name?:string;mode?:string};
type Profile={key:string;title:string;summary:string;database:string;internet_dependency:string;backup_strategy:string;capabilities:string[];environment_template:Record<string,string>};
type GoLive={
  business:{id:number;name:string;deployment_type:string};
  profile:Profile;
  summary:{ready:boolean;score:number;blockers:number;warnings:number;total:number};
  server_checks:Check[];
  business_checks:Check[];
  readiness:{overall:{score:number;completed:number;total:number;blocking:number}};
  integration_checks:Check[];
  next_action:string;
};
type LocalCheck={key:string;status:"ok"|"warning"|"error";message:string;details?:Record<string,unknown>};
type Preflight={ok:boolean;packaged:boolean;platform:string;version:string;checks:LocalCheck[];adapters:Record<string,{selected:string;adapters:Array<{id:string;label:string;status:string;selected:boolean;description:string}>}>};
type BackupResult={ok:boolean;canceled?:boolean;path?:string;sha256?:string;size_bytes?:number;integrity?:string;foreign_key_violations?:number;missing_tables?:string[];error?:string;emergency?:string};

export default function GoLivePage(){
  const [data,setData]=useState<GoLive|null>(null);
  const [profiles,setProfiles]=useState<Profile[]>([]);
  const [local,setLocal]=useState<Preflight|null>(null);
  const [busy,setBusy]=useState(false);
  const [message,setMessage]=useState("");
  const [backup,setBackup]=useState<BackupResult|null>(null);

  const load=async()=>{
    setBusy(true);setMessage("");
    try{
      const [guard,profilePayload]=await Promise.all([
        api<GoLive>("/settings/go-live/"),
        api<{profiles:Profile[]}>("/settings/deployment-profiles/"),
      ]);
      setData(guard);setProfiles(profilePayload.profiles);
      if(typeof window!=="undefined"&&(window as any).cafino?.preflight){
        try{setLocal(await (window as any).cafino.preflight())}catch{}
      }
    }catch(e:any){setMessage(e.message||"خطا در Go-Live Guard");}
    finally{setBusy(false)}
  };
  useEffect(()=>{load()},[]);

  const profile=useMemo(()=>profiles.find(x=>x.key===data?.business.deployment_type)||data?.profile||null,[profiles,data]);
  const allChecks=[...(data?.server_checks||[]),...(data?.business_checks||[]),...(data?.integration_checks||[])];

  const createBackup=async()=>{
    const bridge=(window as any).cafino;if(!bridge?.createBackup)return setMessage("Backup Local فقط داخل اپ Electron قابل اجراست.");
    setBusy(true);setMessage("");try{const result=await bridge.createBackup();setBackup(result);if(result.ok)setMessage("بکاپ ایجاد و integrity آن تأیید شد.");else if(!result.canceled)setMessage(result.error||"بکاپ ناموفق بود.");}finally{setBusy(false)}
  };
  const verifyBackup=async()=>{
    const bridge=(window as any).cafino;if(!bridge?.verifyBackup)return setMessage("اعتبارسنجی فایل Backup فقط داخل Electron در دسترس است.");
    setBusy(true);setMessage("");try{const result=await bridge.verifyBackup();setBackup(result);if(result.ok)setMessage("فایل Backup معتبر و قابل Restore است.");else if(!result.canceled)setMessage(result.error||"Backup معتبر نیست.");}finally{setBusy(false)}
  };
  const restoreBackup=async()=>{
    const bridge=(window as any).cafino;if(!bridge?.restoreBackup)return setMessage("Restore فقط داخل Electron Local در دسترس است.");
    if(!window.confirm("Restore دیتابیس عملیاتی را جایگزین می‌کند. Cafino قبل از Restore یک Emergency Backup می‌سازد. ادامه می‌دهید؟"))return;
    setBusy(true);setMessage("");try{const result=await bridge.restoreBackup();setBackup(result);setMessage(result.ok?"Restore با موفقیت انجام و دیتابیس جدید دوباره Verify شد.":result.error||"Restore ناموفق بود.");}finally{setBusy(false)}
  };

  if(!data)return <div className="card p-6">{message||"در حال محاسبه Go-Live Guard…"}</div>;
  return <div className="space-y-5">
    <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
      <div><div className="text-xs text-[#8d8178]">Production Delivery</div><h2 className="text-3xl font-black">Go-Live Guard</h2><p className="text-sm text-[#8d8178] mt-1">بررسی نهایی محیط اجرا، تنظیمات کسب‌وکار، Integrationها، Backup و Runtime محلی قبل از تحویل به مشتری.</p></div>
      <button className="btn flex items-center gap-2" onClick={load} disabled={busy}><RefreshCw size={16}/>{busy?"در حال بررسی…":"بررسی مجدد"}</button>
    </div>

    <div className={`card p-5 border-2 ${data.summary.ready?"border-emerald-300":"border-amber-300"}`}>
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-start gap-3">{data.summary.ready?<ShieldCheck className="text-emerald-600" size={30}/>:<AlertTriangle className="text-amber-600" size={30}/>}<div><h3 className="font-black text-xl">{data.summary.ready?"آماده تحویل":"هنوز آماده Go-Live نیست"}</h3><p className="text-sm text-[#8d8178] mt-1">{data.summary.blockers} Blocker · {data.summary.warnings} Warning · پروفایل {data.business.deployment_type}</p></div></div>
        <div className="text-left"><b className="text-4xl">{data.summary.score}%</b><div className="text-xs text-[#8d8178]">Delivery score</div></div>
      </div>
      <div className="h-3 rounded-full bg-[#eee6dc] overflow-hidden mt-4"><div className={`h-full ${data.summary.ready?"bg-emerald-600":"bg-amber-500"}`} style={{width:`${data.summary.score}%`}}/></div>
    </div>

    {profile&&<div className="card p-5">
      <div className="flex items-start gap-3"><ServerCog size={24}/><div><h3 className="font-black text-lg">{profile.title}</h3><p className="text-sm text-[#8d8178] leading-6 mt-1">{profile.summary}</p></div></div>
      <div className="grid md:grid-cols-3 gap-3 mt-4"><Info label="Database" value={profile.database}/><Info label="Internet" value={profile.internet_dependency}/><Info label="Backup" value={profile.backup_strategy}/></div>
      <div className="mt-4"><div className="text-sm font-bold mb-2">Environment پیشنهادی First-Run</div><div className="rounded-xl bg-[#211711] text-[#f8f1e8] p-4 overflow-x-auto text-xs leading-6 font-mono" dir="ltr">{Object.entries(profile.environment_template).map(([k,v])=><div key={k}>{k}={v}</div>)}</div></div>
      <div className="flex flex-wrap gap-2 mt-4">{profile.capabilities.map(x=><span className="badge" key={x}>{x}</span>)}</div>
    </div>}

    <div className="grid xl:grid-cols-2 gap-5">
      <section className="card p-5"><h3 className="font-black text-lg flex items-center gap-2"><ServerCog size={20}/> Server & Security</h3><div className="mt-4 space-y-2">{data.server_checks.map(x=><CheckRow key={x.key} check={x}/>)}</div></section>
      <section className="card p-5"><h3 className="font-black text-lg flex items-center gap-2"><Workflow size={20}/> Business & Integrations</h3><div className="mt-4 space-y-2">{[...data.business_checks,...data.integration_checks].map((x,i)=><CheckRow key={`${x.branch||0}-${x.key}-${i}`} check={x}/>)}</div><div className="mt-4 rounded-xl bg-[#f5efe8] p-3 text-sm">Setup Readiness: <b>{data.readiness.overall.score}%</b> · {data.readiness.overall.blocking} مورد ضروری ناقص</div></section>
    </div>

    <div className="grid xl:grid-cols-[1fr_1fr] gap-5">
      <section className="card p-5">
        <h3 className="font-black text-lg flex items-center gap-2"><HardDrive size={20}/> Local Runtime Preflight</h3>
        {local?<><div className="mt-4 space-y-2">{local.checks.map(x=><LocalRow key={x.key} check={x}/>)}</div><div className="mt-4 text-xs text-[#8d8178]">Electron {local.version} · {local.platform} · {local.packaged?"Packaged":"Development"}</div></>:<div className="mt-4 rounded-xl border p-4 text-sm text-[#8d8178]">این صفحه در Web/SaaS باز شده یا Electron Bridge در دسترس نیست؛ Runtime سخت‌افزاری فقط روی دستگاه Local قابل Verify است.</div>}
      </section>
      <section className="card p-5">
        <h3 className="font-black text-lg flex items-center gap-2"><Usb size={20}/> Device Adapter Registry</h3>
        {local?<div className="mt-4 space-y-3">{Object.entries(local.adapters||{}).map(([type,group])=><div key={type} className="border rounded-xl p-3"><div className="flex items-center justify-between"><b>{type}</b><span className="badge">{group.selected}</span></div><div className="text-xs text-[#8d8178] mt-2">{group.adapters.find(x=>x.selected)?.description||"Adapter انتخاب نشده"}</div></div>)}</div>:<div className="mt-4 text-sm text-[#8d8178]">Registry روی Electron Local خوانده می‌شود. POS و Pager تا انتخاب SDK/Protocol برند به‌صورت صریح Manual/Unconfigured باقی می‌مانند.</div>}
      </section>
    </div>

    <section className="card p-5">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between"><div><h3 className="font-black text-lg flex items-center gap-2"><Database size={20}/> Backup / Restore Verification</h3><p className="text-sm text-[#8d8178] mt-1">Backup Local تنها در صورت عبور از SQLite integrity_check، foreign_key_check، schema check و SHA-256 معتبر محسوب می‌شود.</p></div><div className="flex flex-wrap gap-2"><button className="btn" onClick={createBackup} disabled={busy}>ساخت Backup تأییدشده</button><button className="btn" onClick={verifyBackup} disabled={busy}>Verify فایل Backup</button><button className="btn" onClick={restoreBackup} disabled={busy}>Restore تأییدشده</button></div></div>
      {backup&&<div className={`mt-4 rounded-xl border p-4 ${backup.ok?"bg-emerald-50 border-emerald-200":"bg-amber-50 border-amber-200"}`}><b>{backup.ok?"Verification PASS":"Verification FAIL"}</b><div className="grid md:grid-cols-2 gap-2 text-xs mt-2"><span>Integrity: {backup.integrity||"-"}</span><span>FK violations: {backup.foreign_key_violations??"-"}</span><span>Size: {backup.size_bytes?`${Math.round(backup.size_bytes/1024)} KB`:"-"}</span><span className="truncate">SHA-256: {backup.sha256||"-"}</span></div>{backup.path&&<div className="text-xs mt-2 break-all">{backup.path}</div>}{backup.emergency&&<div className="text-xs mt-2 break-all">Emergency backup: {backup.emergency}</div>}{backup.error&&<div className="text-sm text-red-700 mt-2">{backup.error}</div>}</div>}
    </section>

    {message&&<div className="card p-4 text-sm">{message}</div>}
  </div>
}

function Info({label,value}:{label:string;value:string}){return <div className="rounded-xl bg-[#f5efe8] p-3"><div className="text-xs text-[#8d8178]">{label}</div><div className="text-sm leading-6 mt-1">{value}</div></div>}
function CheckRow({check}:{check:Check}){const Icon=check.status==="ok"?CheckCircle2:AlertTriangle;return <div className="border rounded-xl p-3 flex gap-3 items-start"><Icon size={18} className={check.status==="ok"?"text-emerald-600":check.status==="error"?"text-red-600":"text-amber-600"}/><div className="min-w-0"><div className="flex flex-wrap gap-2 items-center"><b className="text-sm">{check.title}</b>{check.branch_name&&<span className="badge">{check.branch_name}</span>}{check.blocking&&<span className="badge text-red-700">Blocker</span>}</div><p className="text-xs text-[#8d8178] leading-6 mt-1">{check.detail}</p></div></div>}
function LocalRow({check}:{check:LocalCheck}){const Icon=check.status==="ok"?CheckCircle2:AlertTriangle;return <div className="border rounded-xl p-3 flex gap-3 items-start"><Icon size={18} className={check.status==="ok"?"text-emerald-600":check.status==="error"?"text-red-600":"text-amber-600"}/><div><b className="text-sm">{check.key}</b><p className="text-xs text-[#8d8178] mt-1">{check.message}</p></div></div>}

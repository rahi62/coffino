"use client";

import {useEffect,useState} from "react";
import {Activity,ArchiveRestore,Download,HardDriveDownload,KeyRound,RefreshCw,ShieldCheck} from "lucide-react";

type ReleaseStatus={
  version:string;
  config:{updateConfigured:boolean;enforceLicense:boolean;backupIntervalHours:number;backupRetentionCount:number;backupMaxAgeDays:number;operationsConfigured?:boolean;telemetryEnabled?:boolean};
  license:{ok:boolean;reason:string;enforced:boolean;installed:boolean;license_id?:string;customer?:string;expires_at?:string|null;machine_hash:string;request_code:string};
  update:{enabled:boolean;status:string;version?:string;percent?:number;error?:string;managedByOps?:boolean;policyنسخه هدف?:string};
  operations?:{enabled:boolean;status:string;lastHeartbeatAt?:string|null;lastDiagnosticAt?:string|null;error?:string;policy?:any}|null;
  pending_update?:{state?:string;from_version?:string;to_version?:string;backup_path?:string}|null;
  backups:{name:string;path:string;mtimeMs:number;size:number}[];
};

export default function ReleasePage(){
  const [data,setData]=useState<ReleaseStatus|null>(null);const[message,setMessage]=useState("");const[busy,setBusy]=useState(false);
  const bridge=()=>typeof window!=="undefined"?(window as any).cafino:null;
  const load=async()=>{const b=bridge();if(!b?.releaseStatus){setData(null);setMessage("این کنسول فقط داخل Cafino Local / Electron در دسترس است.");return;}setBusy(true);try{setData(await b.releaseStatus());setMessage("");}catch(e:any){setMessage(e?.message||String(e))}finally{setBusy(false)}};
  useEffect(()=>{load()},[]);
  const action=async(fn:string,success:string)=>{const b=bridge();if(!b?.[fn])return;setBusy(true);setMessage("");try{const r=await b[fn]();setMessage(r?.ok===false&&!r?.canceled?(r?.error||r?.reason||"عملیات ناموفق بود"):success);await load();}catch(e:any){setMessage(e?.message||String(e))}finally{setBusy(false)}};
  const copy=async()=>{if(data?.license.request_code){await navigator.clipboard.writeText(data.license.request_code);setMessage("کد درخواست کپی شد.")}};
  if(!data)return <div className="card p-6">{message||"در حال خواندن Release Runtime…"}</div>;
  const lic=data.license;const update=data.update;const operations=data.operations;
  return <div className="space-y-5">
    <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between"><div><div className="text-xs text-[#8d8178]">برنامه عملیاتی محلی</div><h2 className="text-3xl font-black">نسخه برنامه و مجوز استفاده</h2><p className="text-sm text-[#8d8178] mt-1">کنترل مجوز استفاده بدون اینترنت، پشتیبان‌گیری، به‌روزرسانی امن و ارتباط اختیاری با بخش سلامت سامانه.</p></div><button className="btn flex items-center gap-2" onClick={load} disabled={busy}><RefreshCw size={16}/>بازخوانی</button></div>
    {message&&<div className="card p-4 text-sm">{message}</div>}

    <div className="grid xl:grid-cols-2 gap-5">
      <section className="card p-5">
        <h3 className="font-black text-lg flex items-center gap-2"><KeyRound size={20}/> مجوز استفاده بدون اینترنت</h3>
        <div className={`mt-4 rounded-xl border p-4 ${lic.ok?"border-emerald-200 bg-emerald-50":"border-amber-200 bg-amber-50"}`}><div className="flex items-center justify-between"><b>{lic.ok?"لایسنس معتبر":"لایسنس معتبر نیست"}</b><span className="badge">{lic.reason}</span></div><div className="text-xs mt-2">Enforcement: {lic.enforced?"فعال":"غیرفعال"}{lic.customer?` · ${lic.customer}`:""}{lic.expires_at?` · Exp: ${new Date(lic.expires_at).toLocaleDateString("fa-IR")}`:""}</div></div>
        <div className="mt-4 text-xs font-bold">کد درخواست</div><div className="mt-2 rounded-xl bg-[#f5efe8] p-3 text-xs break-all" dir="ltr">{lic.request_code}</div>
        <div className="flex gap-2 mt-3"><button className="btn" onClick={copy}>کپی کد درخواست</button><button className="btn" onClick={()=>action("importLicense","لایسنس وارد و Verify شد.")} disabled={busy}>ثبت مجوز استفاده</button></div>
      </section>

      <section className="card p-5">
        <h3 className="font-black text-lg flex items-center gap-2"><HardDriveDownload size={20}/> پشتیبان‌گیری خودکار</h3>
        <div className="grid grid-cols-3 gap-2 mt-4"><Mini label="Interval" value={`${data.config.backupIntervalHours}h`}/><Mini label="Retention" value={`${data.config.backupRetentionCount}`}/><Mini label="Max age" value={`${data.config.backupMaxAgeDays}d`}/></div>
        <button className="btn mt-4" onClick={()=>action("createAutoBackup","Backup خودکارِ فوری ساخته و Verify شد.")} disabled={busy}>همین حالا نسخه پشتیبان بگیر</button>
        <div className="mt-4 space-y-2 max-h-56 overflow-auto">{data.backups.length?data.backups.map(x=><div key={x.path} className="border rounded-xl p-3 text-xs"><b>{x.name}</b><div className="text-[#8d8178] mt-1">{Math.round(x.size/1024)} KB · {new Date(x.mtimeMs).toLocaleString("fa-IR")}</div></div>):<div className="text-sm text-[#8d8178]">هنوز backup زمان‌بندی‌شده‌ای ثبت نشده است.</div>}</div>
      </section>
    </div>

    <section className="card p-5">
      <h3 className="font-black text-lg flex items-center gap-2"><Activity size={20}/> عملیات و سلامت سامانه</h3>
      <div className="grid md:grid-cols-4 gap-2 mt-4"><Mini label="Control Plane" value={data.config.operationsConfigured?"Configured":"Disabled"}/><Mini label="Status" value={operations?.status||"disabled"}/><Mini label="Telemetry" value={data.config.telemetryEnabled?"Opt-in ON":"OFF"}/><Mini label="Policy" value={operations?.policy?.managed?`${operations.policy.channel} · ${operations.policy.rollout_percent}%`:"Unmanaged"}/></div>
      {operations?.lastHeartbeatAt&&<div className="text-xs text-[#8d8178] mt-3">آخرین Heartbeat: {new Date(operations.lastHeartbeatAt).toLocaleString("fa-IR")}</div>}
      {operations?.lastDiagnosticAt&&<div className="text-xs text-[#8d8178] mt-1">آخرین Diagnostic امن: {new Date(operations.lastDiagnosticAt).toLocaleString("fa-IR")}</div>}
      {operations?.error&&<div className="mt-3 rounded-xl bg-amber-50 border border-amber-200 p-3 text-sm">{operations.error}</div>}
      {operations?.policy?.current_blocked&&<div className="mt-3 rounded-xl bg-red-50 border border-red-200 p-3 text-sm"><b>نسخه فعلی مسدود شده است.</b><div className="text-xs mt-1">عملیات اصلی Local ادامه دارد؛ Update/نسخه بازگشت طبق Release Policy انجام شود.</div></div>}
      <div className="flex flex-wrap gap-2 mt-4"><button className="btn" onClick={()=>action("operationsSync","Heartbeat و Release Policy همگام شد.")} disabled={busy||!data.config.operationsConfigured}>همگام‌سازی اکنون</button><a className="btn" href="/operations">داشبورد وضعیت سامانه</a></div>
      <div className="mt-4 flex items-start gap-2 text-xs text-[#8d8178]"><ShieldCheck size={16} className="shrink-0"/>سامانه مرکزی تنها اطلاعات سلامت، شناسه خطا و گزارش فنی مجاز را دریافت می‌کند؛ سفارش‌ها، اطلاعات مشتری، شماره تلفن و فاکتورها ارسال نمی‌شوند.</div>
    </section>

    <section className="card p-5">
      <h3 className="font-black text-lg flex items-center gap-2"><Download size={20}/> به‌روزرسانی خودکار امن</h3>
      <div className="grid md:grid-cols-4 gap-2 mt-4"><Mini label="Current" value={data.version}/><Mini label="Updater" value={data.config.updateConfigured?"Configured":"Disabled"}/><Mini label="Status" value={update.status}/><Mini label="Available" value={update.version||update.policyنسخه هدف||"—"}/></div>
      {typeof update.percent==="number"&&<div className="mt-4"><div className="h-2 rounded-full bg-[#eee6dc] overflow-hidden"><div className="h-full bg-[#211711]" style={{width:`${update.percent}%`}}/></div><div className="text-xs mt-1">{update.percent}%</div></div>}
      {update.managedByOps&&<div className="text-xs mt-3 text-[#8d8178]">انتشار نسخه‌های این دستگاه طبق سیاست سامانه مرکزی کنترل می‌شود.</div>}
      {update.error&&<div className="text-sm text-red-700 mt-3">{update.error}</div>}
      <div className="flex flex-wrap gap-2 mt-4"><button className="btn" onClick={()=>action("checkForUpdate","بررسی Update انجام شد.")} disabled={busy||!update.enabled}>بررسی</button><button className="btn" onClick={()=>action("downloadUpdate","دانلود Update شروع/تکمیل شد.")} disabled={busy||update.status!=="available"}>دریافت</button><button className="btn" onClick={()=>{if(window.confirm("قبل از نصب، Cafino یک Backup تأییدشده می‌سازد و سپس برنامه Restart می‌شود. ادامه می‌دهید؟"))action("installUpdate","نصب Update آغاز شد.")}} disabled={busy||update.status!=="downloaded"}>نصب و راه‌اندازی مجدد</button></div>
      {data.pending_update&&<div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm"><div className="flex items-center gap-2 font-bold"><ArchiveRestore size={18}/> سوابق بازیابی</div><div className="text-xs mt-2">{data.pending_update.from_version} → {data.pending_update.to_version} · {data.pending_update.state}</div>{data.pending_update.backup_path&&<div className="text-xs break-all mt-1" dir="ltr">{data.pending_update.backup_path}</div>}</div>}
      <div className="mt-4 flex items-start gap-2 text-xs text-[#8d8178]"><ShieldCheck size={16} className="shrink-0"/>نصب Update فقط پس از ساخت Backup تأییدشده انجام می‌شود. اگر نسخه جدید بررسی سلامت را پاس نکند، مسیر Backup قبل از Update در سوابق بازیابی حفظ می‌شود.</div>
    </section>
  </div>
}

function Mini({label,value}:{label:string;value:string}){return <div className="rounded-xl bg-[#f5efe8] p-3"><div className="text-[11px] text-[#8d8178]">{label}</div><b className="text-sm break-words">{value}</b></div>}

"use client";
import {useEffect,useMemo,useState} from "react";
import {api} from "@/lib/api";
import {useSettings} from "@/components/settings/settings-context";

const catalog:Record<string,[string,string]>={
 CORE:["هسته کافینو","ضروری برای کارکرد برنامه"],POS:["فروش و صندوق","ثبت سفارش و پرداخت"],DINE_IN:["سالن","میز و سرویس حضوری"],TAKEAWAY:["بیرون‌بر","شماره سفارش و تحویل"],KITCHEN_DISPLAY:["نمایش سفارش‌های آشپزخانه","نمایش سفارش‌های در حال آماده‌سازی"],PAGER:["پیجر","فراخوانی مشتری"],SMS:["پیامک","اطلاع‌رسانی پیامکی"],INVENTORY:["انبار","موجودی و گردش کالا"],RECIPES:["دستور تهیه","مصرف مواد اولیه"],PURCHASING:["خرید","تأمین‌کنندگان و فاکتور خرید"],ACCOUNTING:["مالی مدیریتی","هزینه و سود"],CUSTOMERS:["مشتریان","پرونده مشتریان"],REPORTING:["گزارش‌ها","گزارش فروش و عملکرد"],PRODUCTION:["تولید","قنادی، شیرینی‌پزی و محصولات نهایی"],PRINTING:["چاپ","رسید و برگه آماده‌سازی"],MULTI_BRANCH:["چندشعبه‌ای","مدیریت چند شعبه"],RESERVATION:["رزرو","رزرو میز"],LOYALTY:["باشگاه مشتریان","امتیاز و اعتبار مشتری"],ONLINE_ORDERING:["سفارش آنلاین","منوی عمومی و کد اسکن"],NOTIFICATIONS:["اعلان‌ها","پیام‌های داخل برنامه و اعلان دستگاه"],DELIVERY:["ارسال","محدوده ارسال و پیک"],GIFT_CARD:["کارت هدیه","اعتبار هدیه"],PAYMENT_GATEWAY:["درگاه پرداخت","پرداخت اینترنتی"]
};
const keys=Object.keys(catalog).filter(key=>key!=="CORE");
type Module={id:number;key:string;enabled:boolean};
function initialSelection(modules:Module[]){const rows=new Map(modules.map(m=>[m.key,m.enabled]));return Object.fromEntries(keys.map(key=>[key,rows.get(key)??false])) as Record<string,boolean>;}

export default function BusinessSettings(){
 const {data,refresh}=useSettings();
 const [form,setForm]=useState<any>(null);
 const [selected,setSelected]=useState<Record<string,boolean>|null>(null);
 const [saving,setSaving]=useState(false);
 const [message,setMessage]=useState("");
 const [failedKeys,setFailedKeys]=useState<string[]>([]);
 const [showProfile,setShowProfile]=useState(false);
 useEffect(()=>{if(data)setForm({...data.business})},[data]);
 useEffect(()=>{if(data&&!saving)setSelected(initialSelection(data.modules))},[data,saving]);
 const modules=useMemo(()=>new Map((data?.modules||[]).map(m=>[m.key,m])),[data]);
 const current=useMemo(()=>initialSelection(data?.modules||[]),[data]);
 const pending=keys.filter(key=>selected!==null&&selected[key]!==current[key]);
 const enabledCount=keys.filter(key=>selected?.[key]).length+1;

 const saveProfile=async()=>{
  if(!data||saving)return;
  setSaving(true);setMessage("");
  try{
   await api(`/businesses/${data.business.id}/`,{method:"PATCH",body:JSON.stringify({name:form.name,business_type:form.business_type,deployment_type:form.deployment_type,is_active:form.is_active})});
   setMessage("پروفایل کسب‌وکار ذخیره شد.");
   await refresh();
   window.dispatchEvent(new Event("cafino-permissions-changed"));
  }catch(e){setMessage(e instanceof Error?e.message:"ذخیره پروفایل انجام نشد.")}
  finally{setSaving(false)}
 };
 const saveModules=async()=>{
  if(!data||!selected||!pending.length||saving)return;
  const disabling=pending.filter(key=>current[key]&&!selected[key]);
  if(disabling.length&&!window.confirm(`آیا غیرفعال‌کردن ${disabling.length.toLocaleString("fa-IR")} قابلیت را تأیید می‌کنید؟ داده‌ها حذف نمی‌شوند، اما استفاده از این قابلیت‌ها متوقف خواهد شد.`))return;
  setSaving(true);setMessage("");setFailedKeys([]);
  const failures:string[]=[];
  // Existing API performs individual writes; do not claim the batch is atomic.
  for(const key of pending){
   const m=modules.get(key);
   try{
    if(m)await api(`/business-modules/${m.id}/`,{method:"PATCH",body:JSON.stringify({enabled:selected[key]})});
    else if(selected[key])await api("/business-modules/",{method:"POST",body:JSON.stringify({business:data.business.id,key,enabled:true,config:{}})});
   }catch{failures.push(key)}
  }
  try{await refresh()}catch{ /* SettingsProvider exposes refresh errors through its context. */ }
  window.dispatchEvent(new Event("cafino-permissions-changed"));
  setFailedKeys(failures);
  setMessage(failures.length?`ذخیره ${failures.length.toLocaleString("fa-IR")} مورد انجام نشد. وضعیت ثبت‌شده از سرور دوباره دریافت شد؛ موارد ناموفق را بررسی و دوباره انتخاب کنید.`:"تغییرات ماژول‌ها ذخیره شدند.");
  setSaving(false);
 };
 if(!data||!form||!selected)return <div role="status" className="card p-4">در حال دریافت تنظیمات کسب‌وکار…</div>;
 return <div className="min-w-0 space-y-4">
  <header><h2 className="text-2xl font-black">مدیریت قابلیت‌های کسب‌وکار</h2><p className="mt-1 text-sm text-[#8d8178]">قابلیت‌ها را انتخاب کنید و یک‌جا ذخیره کنید. خاموش‌کردن قابلیت، اطلاعات آن را حذف نمی‌کند.</p></header>
  {message&&<div role={failedKeys.length?"alert":"status"} className="card p-3 text-sm">{message}</div>}
  <section className="card p-3 sm:p-5" aria-label="قابلیت‌های کسب‌وکار">
    <div className="flex flex-wrap items-center justify-between gap-2"><h3 className="text-lg font-black">قابلیت‌های فعال</h3><span className="badge">{enabledCount.toLocaleString("fa-IR")} فعال</span></div>
    <div className="mt-3 flex flex-wrap gap-2">
      <button type="button" disabled={saving} onClick={()=>setSelected(Object.fromEntries(keys.map(key=>[key,true])))} className="btn min-h-11 text-sm">انتخاب همه</button>
      <button type="button" disabled={saving} onClick={()=>setSelected(Object.fromEntries(keys.map(key=>[key,false])))} className="btn min-h-11 text-sm">لغو انتخاب‌ها</button>
      <button type="button" disabled={saving||!pending.length} onClick={()=>setSelected({...current})} className="btn min-h-11 text-sm disabled:opacity-50">بازگرداندن تغییرات</button>
    </div>
    <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2 xl:grid-cols-3">
      {Object.entries(catalog).map(([key,[title,description]])=>{
        const active=key==="CORE"||Boolean(selected[key]);
        return <label key={key} className={`flex min-h-14 cursor-pointer items-center gap-3 rounded-xl border px-3 py-3 ${active?"border-emerald-300 bg-emerald-50/50":"border-[#eadfd3] bg-white"} ${key==="CORE"?"cursor-not-allowed":""}`}>
          <input type="checkbox" className="h-5 w-5 shrink-0 accent-[#b9792d]" disabled={saving||key==="CORE"} checked={active} onChange={e=>setSelected(prev=>({...prev,[key]:e.target.checked}))} aria-label={title}/>
          <span className="min-w-0 flex-1"><b className="block text-sm">{title}</b><span className="mt-0.5 block text-xs text-[#8d8178]">{description}</span></span>
          {key==="CORE"&&<span className="shrink-0 text-xs text-[#8d8178]">همیشگی</span>}
        </label>;
      })}
    </div>
  </section>
  <div className="sticky z-20 rounded-2xl border border-[#eadfd3] bg-[#fffdf9]/95 p-3 shadow-lg backdrop-blur bottom-[calc(5rem+env(safe-area-inset-bottom,0px))] md:bottom-3">
    <div className="flex items-center justify-between gap-3"><p className="text-sm font-bold">{pending.length?`${pending.length.toLocaleString("fa-IR")} تغییر ذخیره‌نشده`:"همه تغییرات ذخیره شده‌اند"}</p><button type="button" disabled={saving||!pending.length} onClick={()=>void saveModules()} className="btn btn-primary min-h-12 shrink-0 font-bold disabled:opacity-50">{saving?"در حال ذخیره…":"ذخیره تغییرات"}</button></div>
  </div>
  <section className="card p-4 sm:p-5"><button type="button" aria-expanded={showProfile} onClick={()=>setShowProfile(v=>!v)} className="flex min-h-11 w-full items-center justify-between text-right font-black"><span>اطلاعات پایه کسب‌وکار</span><span aria-hidden="true">{showProfile?"−":"+"}</span></button>
   {showProfile&&<div className="mt-3 space-y-3"><div className="grid gap-3 md:grid-cols-2">
    <label className="text-sm">نام مجموعه<input className="mt-1 w-full rounded-xl border p-3" value={form.name} onChange={e=>setForm({...form,name:e.target.value})}/></label>
    <label className="text-sm">نوع کسب‌وکار<select className="mt-1 w-full rounded-xl border p-3" value={form.business_type} onChange={e=>setForm({...form,business_type:e.target.value})}><option value="CAFE">کافه</option><option value="RESTAURANT">رستوران</option><option value="FAST_FOOD">فست‌فود</option><option value="BAKERY">نانوایی</option><option value="PASTRY">قنادی</option><option value="CATERING">تهیه غذا</option><option value="HOTEL_RESTAURANT">رستوران هتل</option><option value="OTHER">سایر</option></select></label>
    <label className="text-sm">روش راه‌اندازی<select className="mt-1 w-full rounded-xl border p-3" value={form.deployment_type} onChange={e=>setForm({...form,deployment_type:e.target.value})}><option value="LOCAL">محلی</option><option value="SAAS">ابری</option><option value="DEDICATED">اختصاصی</option></select></label>
    <label className="flex min-h-12 items-center gap-3 rounded-xl border p-3 text-sm"><input type="checkbox" checked={!!form.is_active} onChange={e=>setForm({...form,is_active:e.target.checked})}/> کسب‌وکار فعال است</label>
   </div><button type="button" disabled={saving} onClick={()=>void saveProfile()} className="btn btn-primary min-h-12 disabled:opacity-50">ذخیره پروفایل</button></div>}
  </section>
 </div>;
}

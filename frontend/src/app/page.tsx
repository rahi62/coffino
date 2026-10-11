"use client";

import Link from "next/link";
import {useCallback,useEffect,useState} from "react";
import {api} from "@/lib/api";
import {dashboardActions,permittedActions} from "@/lib/dashboard-actions.mjs";

type DashboardData={sales_today:number;orders_today:number;open_orders:number;ready_orders:number;low_stock:number|null;month_revenue:number|null;month_net_profit:number|null;break_even_revenue:number|null;break_even_orders:number|null};
type SetupCheck={key:string;title:string;status:"done"|"missing"|"warning";required:boolean;detail:string;href:string};
type Readiness={overall:{blocking:number};business:{checks:SetupCheck[]};branches:Array<{branch:number;name:string;checks:SetupCheck[]}>};
const format=(value:number|null|undefined)=>Number(value??0).toLocaleString("fa-IR");

export default function Dashboard(){
  const [permissions,setPermissions]=useState<Record<string,boolean>|null>(null);
  const [data,setData]=useState<DashboardData|null>(null);
  const [readiness,setReadiness]=useState<Readiness|null>(null);
  const [permissionError,setPermissionError]=useState("");
  const [dashboardError,setDashboardError]=useState("");
  const [readinessError,setReadinessError]=useState("");
  const [loading,setLoading]=useState(true);
  const [refreshing,setRefreshing]=useState(false);
  const [updatedAt,setUpdatedAt]=useState<Date|null>(null);

  const load=useCallback(async()=>{
    setRefreshing(true);setPermissions(null);
    setPermissionError("");setDashboardError("");setReadinessError("");
    try{
      // Permissions must resolve first: a failed permission request must never unlock actions.
      const result=await api<{permissions:Record<string,boolean>}>("/permissions/me/");
      if(!result.permissions||typeof result.permissions!=="object")throw new Error("پاسخ دسترسی‌ها معتبر نیست.");
      const perms=result.permissions;
      setPermissions(perms);
      const jobs:Promise<unknown>[]=[];
      if(perms["orders.view"]||perms["reports.view"]){
        jobs.push(api<DashboardData>("/dashboard/").then(x=>{setData(x);setUpdatedAt(new Date())}).catch(e=>{
          setData(null);setDashboardError(e instanceof Error?e.message:"دریافت آمار ممکن نشد.");
        }));
      }else{setData(null);}
      if(perms["settings.manage"]){
        jobs.push(api<Readiness>("/settings/readiness/").then(setReadiness).catch(e=>{
          setReadiness(null);setReadinessError(e instanceof Error?e.message:"وضعیت راه‌اندازی قابل دریافت نیست.");
        }));
      }else{setReadiness(null);}
      await Promise.all(jobs);
    }catch(e){
      setPermissions(null);setData(null);setReadiness(null);
      setPermissionError(e instanceof Error?e.message:"بررسی سطح دسترسی انجام نشد.");
    }finally{setLoading(false);setRefreshing(false);}
  },[]);
  useEffect(()=>{void load()},[load]);
  useEffect(()=>{
    const refreshPermissions=()=>{void load()};
    window.addEventListener("cafino-permissions-changed",refreshPermissions);
    return()=>window.removeEventListener("cafino-permissions-changed",refreshPermissions);
  },[load]);

  const actions=permittedActions(dashboardActions,permissions);
  const mayCreate=permissions?.["orders.create"]===true;
  const checks=readiness?[...readiness.business.checks,...readiness.branches.flatMap(b=>b.checks)]:[];
  const needed=checks.filter(x=>x.status!=="done"&&x.required);
  const setupActions=needed.filter(x=>x.href&&x.href.startsWith("/settings/")).slice(0,4);
  const cards=data?[
    {label:"فروش امروز",value:`${format(data.sales_today)} ریال`,tone:"text-[#b9792d]"},
    {label:"سفارش امروز",value:format(data.orders_today),tone:"text-[#2b1e16]"},
    {label:"در حال آماده‌سازی",value:format(data.open_orders),tone:"text-amber-700"},
    {label:"آمادهٔ تحویل",value:format(data.ready_orders),tone:"text-emerald-700"},
  ]:[];

  return <div className="min-w-0 space-y-4 md:space-y-5">
    <header className="rounded-[22px] bg-[#211711] p-4 text-white shadow-[0_12px_32px_rgba(33,23,17,.16)] sm:p-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0"><p className="text-xs text-[#dfbd93]">مدیریت عملیات روزانه</p><h1 className="mt-1 text-2xl font-black sm:text-3xl">داشبورد کافینو</h1></div>
        <button type="button" disabled={refreshing} onClick={()=>void load()} className="min-h-11 self-start rounded-xl bg-white/10 px-4 text-sm text-white hover:bg-white/20 disabled:opacity-50 sm:self-auto"> {refreshing?"در حال به‌روزرسانی…":"به‌روزرسانی"} </button>
      </div>
      <div className="mt-4">
        {loading||!permissions?<span className="flex min-h-12 items-center rounded-2xl bg-white/10 px-4 text-sm" role="status">{permissionError?"امکان بررسی مجوز وجود ندارد.":"در حال بررسی دسترسی به ثبت سفارش…"}</span>
          :mayCreate?<Link href="/pos" className="flex min-h-14 w-full items-center justify-center rounded-2xl bg-[#e5ad62] px-5 text-center text-lg font-black text-[#211711] transition hover:bg-[#f5c77f] focus-visible:outline focus-visible:outline-4 focus-visible:outline-offset-2 focus-visible:outline-white sm:max-w-sm">+ ثبت سفارش جدید</Link>
          :<p className="rounded-xl bg-white/10 p-3 text-sm">مجوز ثبت سفارش برای حساب فعلی فعال نیست.</p>}
      </div>
      {updatedAt&&<p className="mt-3 text-xs text-white/60">به‌روزرسانی آمار: {updatedAt.toLocaleTimeString("fa-IR",{hour:"2-digit",minute:"2-digit"})}</p>}
    </header>

    {permissionError&&<section role="alert" className="card border-red-200 p-4 text-red-800"><b>دسترسی‌ها بارگذاری نشدند.</b><p className="mt-1 text-sm">{permissionError}</p><button type="button" onClick={()=>void load()} className="btn mt-3 min-h-11">تلاش دوباره</button></section>}

    <section aria-label="دسترسی سریع" className="card p-4 sm:p-5">
      <h2 className="text-lg font-black">دسترسی سریع</h2>
      <p className="mt-1 text-xs text-[#8d8178]">عملیات مجاز و فعال کسب‌وکار، بدون جست‌وجو در منو</p>
      {!permissions?<p role="status" className="mt-4 text-sm text-[#8d8178]">در انتظار دریافت مجوزها…</p>
        :actions.length?<div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-3 xl:grid-cols-4">{actions.map(action=><Link key={action.href} href={action.href} className={`flex min-h-16 flex-col justify-center rounded-xl border p-3 text-sm transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#b9792d] ${action.href==="/pos"?"border-[#b9792d] bg-[#fbefd9] font-black":"border-[#eadfd3] bg-[#fffdf9] hover:bg-[#f7f0e8]"}`}><span className="font-bold">{action.label}</span><span className="mt-1 text-xs text-[#8d8178]">{action.detail}</span></Link>)}</div>
        :<p className="mt-4 text-sm text-[#8d8178]">میان‌بری با سطح دسترسی فعلی در دسترس نیست.</p>}
    </section>

    {readiness&&needed.length>0&&<section aria-label="شروع کار کسب‌وکار" className="card p-4 sm:p-5">
      <h2 className="text-lg font-black">برای شروع کار آماده شو</h2>
      <p className="mt-1 text-sm text-[#8d8178]">این موارد مستقیماً از وضعیت راه‌اندازی ثبت‌شده در سرور دریافت شده‌اند.</p>
      <div className="mt-3 grid gap-2 sm:grid-cols-2">{setupActions.map(check=><Link href={check.href} key={check.key} className="flex min-h-12 flex-col justify-center rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm hover:bg-amber-100"><b>{check.title}</b><span className="mt-1 text-xs text-amber-900">{check.detail}</span></Link>)}</div>
      {permissions?.["business.manage"]&&<Link href="/settings/onboarding" className="mt-3 inline-flex min-h-11 items-center font-bold text-[#89571e] underline underline-offset-4">راهنمای کامل راه‌اندازی</Link>}
    </section>}
    {readinessError&&permissions?.["settings.manage"]&&<p role="status" className="text-sm text-amber-800">وضعیت راه‌اندازی قابل بررسی نبود: {readinessError}</p>}

    {dashboardError&&<section role="alert" className="card border-amber-300 p-4 text-sm text-amber-900">آمار داشبورد دریافت نشد: {dashboardError} <button type="button" onClick={()=>void load()} className="mr-2 min-h-11 font-bold underline">تلاش دوباره</button></section>}
    {data&&<section className="grid grid-cols-2 gap-3 lg:grid-cols-4" aria-label="آمار روزانه">{cards.map(card=><article className="card min-w-0 p-4" key={card.label}><p className="text-sm text-[#8d8178]">{card.label}</p><b className={`mt-2 block break-words text-lg sm:text-2xl ${card.tone}`}>{card.value}</b></article>)}</section>}
    {data&&permissions?.["inventory.view"]&&<section className="card p-4"><h2 className="font-bold">کمبود موجودی</h2><p className="mt-2 text-lg font-black">{data.low_stock===null?"اطلاعات موجودی در دسترس نیست":format(data.low_stock)}</p></section>}
    {data&&permissions?.["reports.view"]&&<section className="grid gap-3 lg:grid-cols-3" aria-label="گزارش‌های مالی">
      <article className="card p-4"><p className="text-sm text-[#8d8178]">فروش خالص ماه</p><b className="mt-2 block text-xl">{data.month_revenue===null?"داده موجود نیست":`${format(data.month_revenue)} ریال`}</b></article>
      <article className="card p-4"><p className="text-sm text-[#8d8178]">سود خالص مدیریتی</p><b className="mt-2 block text-xl">{data.month_net_profit===null?"داده موجود نیست":`${format(data.month_net_profit)} ریال`}</b></article>
      <article className="card p-4"><p className="text-sm text-[#8d8178]">نقطه سربه‌سر</p><b className="mt-2 block text-xl">{data.break_even_revenue===null?"نیازمند داده بیشتر":`${format(data.break_even_revenue)} ریال`}</b></article>
    </section>}
    {data&&permissions?.["orders.view"]&&<section className="card p-4 sm:p-5"><h2 className="text-lg font-black">چرخه سفارش</h2><div className="mt-3 grid gap-2 sm:grid-cols-2"><Link href="/orders" className="flex min-h-12 items-center justify-between rounded-xl bg-[#f7f0e8] p-3">سفارش‌های امروز <b>{format(data.orders_today)}</b></Link>{permissions["kitchen.view"]&&<Link href="/kitchen" className="flex min-h-12 items-center justify-between rounded-xl bg-amber-50 p-3">در حال آماده‌سازی <b>{format(data.open_orders)}</b></Link>}</div></section>}
  </div>;
}

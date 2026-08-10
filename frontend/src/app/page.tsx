"use client";

import Link from "next/link";
import {useEffect, useState} from "react";
import {api} from "@/lib/api";

type DashboardData = {sales_today:number; orders_today:number; open_orders:number; ready_orders:number; low_stock:number|null; month_revenue:number|null; month_net_profit:number|null; break_even_revenue:number|null; break_even_orders:number|null};
const money = (value:number|null|undefined) => Number(value || 0).toLocaleString("fa-IR");
const number = (value:number|null|undefined) => Number(value || 0).toLocaleString("fa-IR");

export default function Dashboard() {
  const [data, setData] = useState<DashboardData>({sales_today:0, orders_today:0, open_orders:0, ready_orders:0, low_stock:null, month_revenue:null, month_net_profit:null, break_even_revenue:null, break_even_orders:null});
  const [permissions, setPermissions] = useState<Record<string,boolean>>({});
  const [updatedAt, setUpdatedAt] = useState<Date|null>(null);
  const load = async () => {
    const [nextPermissions, nextDashboard] = await Promise.all([api<any>("/permissions/me/"), api<DashboardData>("/dashboard/")]);
    setPermissions(nextPermissions.permissions || {}); setData(nextDashboard); setUpdatedAt(new Date());
  };
  useEffect(() => { void load().catch(() => {}); }, []);
  const cards = [
    {label:"فروش امروز", value:`${money(data.sales_today)} ریال`, tone:"text-[#b9792d]", hint:"سفارش‌های تسویه‌شده"},
    {label:"سفارش امروز", value:number(data.orders_today), tone:"text-[#2b1e16]", hint:"ثبت‌شده در شعبهٔ فعال"},
    {label:"در حال آماده‌سازی", value:number(data.open_orders), tone:"text-amber-700", hint:"نیازمند پیگیری عملیات"},
    {label:"آمادهٔ تحویل", value:number(data.ready_orders), tone:"text-emerald-700", hint:"آمادهٔ اعلام یا تحویل"},
  ];
  if (permissions["inventory.view"]) cards.push({label:"کمبود موجودی", value:number(data.low_stock), tone:data.low_stock ? "text-red-700" : "text-emerald-700", hint:data.low_stock ? "نیازمند تأمین" : "موجودی کنترل‌شده"});
  const actions = [
    permissions["orders.create"] && {href:"/pos", label:"فروش جدید", detail:"ثبت سریع سفارش", primary:true},
    permissions["cashier.use"] && {href:"/cashier", label:"صندوق", detail:"شروع یا کنترل شیفت"},
    permissions["purchasing.manage"] && {href:"/purchasing", label:"ثبت خرید", detail:"ورود خرید و هزینه"},
    permissions["reports.view"] && {href:"/reports", label:"گزارش فروش", detail:"بررسی عملکرد امروز"},
  ].filter(Boolean) as {href:string;label:string;detail:string;primary?:boolean}[];

  return <div className="space-y-5"><header className="overflow-hidden rounded-[24px] bg-[#211711] p-6 text-white shadow-[0_12px_32px_rgba(33,23,17,.16)]"><div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><div><p className="text-sm text-[#dfbd93]">نمای عملیاتی امروز</p><h1 className="mt-1 text-3xl font-black">مرکز فرمان کافینو</h1><p className="mt-2 text-sm text-[#e9ddd1]">تصمیم‌های روزانه، فروش و صف آماده‌سازی در یک نگاه.</p></div><div className="flex items-center gap-3"><div className="text-xs text-[#e9ddd1]">{updatedAt ? `به‌روزرسانی ${updatedAt.toLocaleTimeString("fa-IR", {hour:"2-digit", minute:"2-digit"})}` : "در حال دریافت اطلاعات"}</div><button type="button" className="rounded-xl bg-white/10 px-3 py-2 text-sm hover:bg-white/20" onClick={() => void load().catch(() => {})}>به‌روزرسانی</button></div></div></header><section className={`grid gap-3 ${cards.length === 5 ? "xl:grid-cols-5" : "md:grid-cols-4"}`}>{cards.map(card => <article className="card p-4" key={card.label}><div className="text-sm text-[#8d8178]">{card.label}</div><div className={`mt-2 text-2xl font-black ${card.tone}`}>{card.value}</div><div className="mt-2 text-xs text-[#8d8178]">{card.hint}</div></article>)}</section>{permissions["reports.view"] && <section className="grid gap-4 lg:grid-cols-3"><article className="card p-5"><div className="text-sm text-[#8d8178]">فروش خالص ماه</div><b className="mt-2 block text-xl">{money(data.month_revenue)} ریال</b><p className="mt-2 text-xs text-[#8d8178]">بر پایهٔ فروش‌های ثبت‌شدهٔ این ماه</p></article><article className="card p-5"><div className="text-sm text-[#8d8178]">سود خالص مدیریتی ماه</div><b className={`mt-2 block text-xl ${Number(data.month_net_profit) < 0 ? "text-red-700" : "text-emerald-700"}`}>{money(data.month_net_profit)} ریال</b><p className="mt-2 text-xs text-[#8d8178]">فروش، هزینه و بهای مواد اولیه</p></article><article className="card p-5"><div className="text-sm text-[#8d8178]">نقطهٔ سربه‌سر</div><b className="mt-2 block text-xl">{data.break_even_revenue == null ? "نیازمند دادهٔ بیشتر" : `${money(data.break_even_revenue)} ریال`}</b><p className="mt-2 text-xs text-[#8d8178]">{data.break_even_orders == null ? "برای محاسبه، هزینه و فروش کامل شود." : `${Math.ceil(Number(data.break_even_orders)).toLocaleString("fa-IR")} سفارش تقریبی`}</p></article></section>}<section className="grid gap-5 lg:grid-cols-[minmax(0,1.15fr)_minmax(320px,.85fr)]"><article className="card p-5"><div className="flex items-center justify-between gap-3"><div><h2 className="text-xl font-black">عملیات سریع</h2><p className="mt-1 text-sm text-[#8d8178]">مسیرهای پرتکرار بدون جست‌وجو در منو</p></div><span className="badge bg-[#f7f0e8]">امروز</span></div><div className="mt-4 grid gap-3 sm:grid-cols-2">{actions.length ? actions.map(action => <Link className={`rounded-2xl border p-4 transition hover:-translate-y-0.5 ${action.primary ? "border-[#b9792d] bg-[#b9792d] text-white" : "border-[#eadfd3] bg-[#fffdf9] hover:bg-[#f7f0e8]"}`} href={action.href} key={action.href}><b className="block">{action.label}</b><span className={`mt-1 block text-sm ${action.primary ? "text-white/80" : "text-[#8d8178]"}`}>{action.detail}</span></Link>) : <p className="text-sm text-[#8d8178]">عملیاتی متناسب با سطح دسترسی شما در دسترس نیست.</p>}</div></article><article className="card p-5"><h2 className="text-xl font-black">چرخهٔ سفارش</h2><p className="mt-1 text-sm text-[#8d8178]">برای هماهنگی تیم، وضعیت‌ها را از همین مسیر دنبال کنید.</p><div className="mt-5 space-y-3"><Link className="flex items-center justify-between rounded-xl bg-[#f7f0e8] p-3 hover:bg-[#eee2d4]" href="/orders"><span>سفارش‌های ثبت‌شده</span><b>{number(data.orders_today)}</b></Link><Link className="flex items-center justify-between rounded-xl bg-amber-50 p-3 hover:bg-amber-100" href="/kitchen"><span>در حال آماده‌سازی</span><b className="text-amber-800">{number(data.open_orders)}</b></Link><Link className="flex items-center justify-between rounded-xl bg-emerald-50 p-3 hover:bg-emerald-100" href="/orders"><span>آمادهٔ تحویل</span><b className="text-emerald-800">{number(data.ready_orders)}</b></Link></div></article></section></div>;
}

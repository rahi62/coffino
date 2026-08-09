"use client";
import {useEffect,useState} from "react";
import {api} from "@/lib/api";

export default function Dashboard(){
  const [d,setD]=useState<any>({
    sales_today:0,orders_today:0,open_orders:0,ready_orders:0,low_stock:null,
    month_revenue:null,month_net_profit:null,break_even_revenue:null,break_even_orders:null
  });
  const [perms,setPerms]=useState<Record<string,boolean>>({});

  useEffect(()=>{
    api<any>("/permissions/me/").then(x=>setPerms(x.permissions||{})).catch(()=>{});
    api<any>("/dashboard/").then(setD).catch(()=>{});
  },[]);

  const cards:any[]=[
    ["فروش امروز",Number(d.sales_today||0).toLocaleString("fa-IR")+" ریال"],
    ["سفارش امروز",d.orders_today||0],
    ["سفارش باز",d.open_orders||0],
    ["آماده تحویل",d.ready_orders||0],
  ];
  if(perms["inventory.view"])cards.push(["کمبود موجودی",d.low_stock??0]);

  return <div>
    <h1 className="text-3xl font-black mb-1">مرکز فرمان کافینو</h1>
    <p className="text-[#8d8178] mb-6">عملیات زنده بر اساس سطح دسترسی شما</p>

    <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
      {cards.map(([t,v])=><div className="card p-5" key={String(t)}>
        <div className="text-sm text-[#8d8178]">{t}</div>
        <div className="text-2xl font-black mt-2">{v}</div>
      </div>)}
    </div>

    {perms["reports.view"]&&<div className="grid md:grid-cols-3 gap-4 mt-5">
      <div className="card p-5">
        <div className="text-[#8d8178]">فروش خالص ماه</div>
        <b className="text-xl">{Number(d.month_revenue||0).toLocaleString("fa-IR")} ریال</b>
      </div>
      <div className="card p-5">
        <div className="text-[#8d8178]">سود خالص مدیریتی ماه</div>
        <b className="text-xl">{Number(d.month_net_profit||0).toLocaleString("fa-IR")} ریال</b>
      </div>
      <div className="card p-5">
        <div className="text-[#8d8178]">نقطه سربه‌سر</div>
        <b className="text-xl">
          {d.break_even_revenue==null?"نیازمند داده بیشتر":Number(d.break_even_revenue).toLocaleString("fa-IR")+" ریال"}
        </b>
        <div className="text-xs text-[#8d8178] mt-1">
          {d.break_even_orders==null?"":Math.ceil(Number(d.break_even_orders)).toLocaleString("fa-IR")+" سفارش تقریبی"}
        </div>
      </div>
    </div>}

    <div className="grid md:grid-cols-2 gap-5 mt-6">
      <div className="card p-5">
        <h2 className="font-black text-xl mb-4">عملیات سریع</h2>
        <div className="grid grid-cols-2 gap-3">
          {perms["orders.create"]&&<a className="btn btn-primary text-center" href="/pos">فروش جدید</a>}
          {perms["purchasing.manage"]&&<a className="btn text-center" href="/purchasing">ثبت خرید</a>}
          {perms["cashier.use"]&&<a className="btn text-center" href="/cashier">صندوق</a>}
          {perms["reports.view"]&&<a className="btn text-center" href="/reports">تحلیل سود</a>}
        </div>
      </div>
      <div className="card p-5">
        <h2 className="font-black text-xl">کنترل دسترسی</h2>
        <p className="leading-8 text-[#6f6259] mt-3">
          Dashboard و مسیرهای سریع بر اساس Permission Matrix کاربر نمایش داده می‌شوند؛ داده مالی و انبار برای نقش‌های بدون مجوز ارسال یا نمایش داده نمی‌شود.
        </p>
      </div>
    </div>
  </div>
}

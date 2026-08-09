"use client";
import {useEffect,useState} from "react";import {api} from "@/lib/api";
const money=(v:any)=>Number(v||0).toLocaleString("fa-IR");
export default function Analytics(){const [d,setD]=useState<any>({by_item:[],by_category:[],by_hour:[],cashiers:[]});useEffect(()=>{api<any>("/reports/sales/").then(setD).catch(()=>{})},[]);
return <div><h1 className="text-3xl font-black mb-2">تحلیل فروش و عملکرد</h1><p className="text-[#8d8178] mb-6">آیتم، دسته‌بندی، ساعت فروش و عملکرد صندوق‌دار</p>
<div className="grid md:grid-cols-2 gap-5">
<section className="card p-5"><h2 className="font-black text-xl mb-3">محصولات پرفروش</h2>{d.by_item.map((x:any)=><div className="flex justify-between border-b py-2" key={x.product_name}><span>{x.product_name} × {x.quantity}</span><b>{money(x.revenue)}</b></div>)}</section>
<section className="card p-5"><h2 className="font-black text-xl mb-3">دسته‌بندی‌ها</h2>{d.by_category.map((x:any,i:number)=><div className="flex justify-between border-b py-2" key={i}><span>{x.product__category__name||"بدون دسته"}</span><b>{money(x.revenue)}</b></div>)}</section>
<section className="card p-5"><h2 className="font-black text-xl mb-3">فروش ساعتی</h2>{d.by_hour.map((x:any)=><div className="flex justify-between border-b py-2" key={x.hour}><span>ساعت {x.hour}:00 — {x.orders} سفارش</span><b>{money(x.revenue)}</b></div>)}</section>
<section className="card p-5"><h2 className="font-black text-xl mb-3">عملکرد صندوق‌دار</h2>{d.cashiers.map((x:any,i:number)=><div className="border-b py-2" key={i}><div className="flex justify-between"><b>{x.received_by__first_name||x.received_by__username||"نامشخص"}</b><b>{money(x.net_collected)}</b></div><div className="text-xs text-[#8d8178]">تراکنش {x.transactions} | Refund {money(x.refunds)}</div></div>)}</section>
</div></div>}

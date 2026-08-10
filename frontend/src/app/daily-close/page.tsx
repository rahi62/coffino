"use client";

import {useEffect,useState} from "react";
import {api} from "@/lib/api";

export default function DailyClose(){
 const [counted,setCounted]=useState("0"),[rows,setRows]=useState<any[]>([]),[msg,setMsg]=useState("");
 const load=()=>api<any[]>("/daily-closings/").then(setRows);
 useEffect(()=>{load().catch(()=>{})},[]);
 const close=async()=>{try{const d:any=await api("/daily-close/",{method:"POST",body:JSON.stringify({counted_cash:counted})});setMsg(`روز بسته شد؛ اختلاف صندوق ${Number(d.cash_difference).toLocaleString("fa-IR")} ریال`);load()}catch(e:any){setMsg(e.message)}};
 return <div><h1 className="mb-2 text-3xl font-black">بستن روز مالی</h1><p className="mb-5 text-[#8d8178]">نمای نهایی فروش، برگشت‌ها، روش پرداخت و مغایرت وجه نقد</p><div className="card mb-6 max-w-xl p-5"><label className="mb-2 block">وجه نقد شمارش‌شده</label><input className="btn w-full border bg-white" value={counted} onChange={e=>setCounted(e.target.value)}/><button className="btn btn-primary mt-3 w-full" onClick={close}>بستن روز جاری</button>{msg&&<div className="mt-3">{msg}</div>}</div><div className="card overflow-x-auto"><table className="w-full min-w-[700px] text-sm"><thead className="bg-[#eee6dc]"><tr><th className="p-3">روز</th><th>فروش خالص</th><th>نقد</th><th>کارت‌خوان</th><th>مورد انتظار</th><th>شمارش</th><th>اختلاف</th></tr></thead><tbody>{rows.map(x=><tr className="border-t" key={x.id}><td className="p-3">{x.business_date}</td><td>{Number(x.net_sales).toLocaleString("fa-IR")}</td><td>{Number(x.cash_sales).toLocaleString("fa-IR")}</td><td>{Number(x.pos_sales).toLocaleString("fa-IR")}</td><td>{Number(x.expected_cash).toLocaleString("fa-IR")}</td><td>{Number(x.counted_cash).toLocaleString("fa-IR")}</td><td>{Number(x.cash_difference).toLocaleString("fa-IR")}</td></tr>)}</tbody></table></div></div>
}

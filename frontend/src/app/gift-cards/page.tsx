"use client";

import {useEffect,useState} from "react";
import {api} from "@/lib/api";

export default function GiftCards(){
 const [rows,setRows]=useState<any[]>([]),[msg,setMsg]=useState(""),[last,setLast]=useState(""),[f,setF]=useState<any>({amount:"1000000",recipient_name:"",purchaser_name:"",note:""});
 const load=()=>api<any[]>("/gift-cards/").then(setRows);
 useEffect(()=>{load().catch(e=>setMsg(e.message))},[]);
 const issue=async()=>{const x:any=await api("/gift-cards/issue/",{method:"POST",body:JSON.stringify({...f,amount:Number(f.amount)})});setLast(x.code);setMsg("✓ کارت صادر شد؛ کد فقط همین‌جا نمایش داده می‌شود");load()};
 return <div><h1 className="mb-2 text-3xl font-black">کارت هدیه</h1><p className="mb-5 text-[#8d8178]">کد اصلی هش می‌شود و فقط ۴ رقم آخر در مدیریت قابل مشاهده است.</p>{msg&&<div className="card mb-4 p-3">{msg}</div>}{last&&<div className="card mb-5 border-2 border-[#b9792d] p-5"><div className="text-sm">کد کارت جدید</div><code className="text-2xl font-black">{last}</code></div>}<div className="grid gap-5 md:grid-cols-[360px_1fr]"><div className="card space-y-2 p-4"><input className="w-full rounded-xl border p-2" placeholder="مبلغ" value={f.amount} onChange={e=>setF({...f,amount:e.target.value})}/><input className="w-full rounded-xl border p-2" placeholder="نام دریافت‌کننده" value={f.recipient_name} onChange={e=>setF({...f,recipient_name:e.target.value})}/><input className="w-full rounded-xl border p-2" placeholder="خریدار" value={f.purchaser_name} onChange={e=>setF({...f,purchaser_name:e.target.value})}/><input className="w-full rounded-xl border p-2" placeholder="یادداشت" value={f.note} onChange={e=>setF({...f,note:e.target.value})}/><button className="btn btn-primary w-full" onClick={issue}>صدور کارت</button></div><div className="card overflow-x-auto"><table className="w-full min-w-[560px]"><thead><tr><th className="p-3">کارت</th><th>اولیه</th><th>مانده</th><th>گیرنده</th><th>وضعیت</th></tr></thead><tbody>{rows.map(x=><tr className="border-t" key={x.id}><td className="p-3 font-mono">{x.masked_code}</td><td>{Number(x.initial_balance).toLocaleString("fa-IR")}</td><td>{Number(x.balance).toLocaleString("fa-IR")}</td><td>{x.recipient_name||"—"}</td><td>{x.is_active?"فعال":"غیرفعال"}</td></tr>)}</tbody></table></div></div></div>
}

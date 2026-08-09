"use client";
import {useEffect,useState} from "react";import {api} from "@/lib/api";
const n=(v:any)=>Number(v||0).toLocaleString("fa-IR");
export default function InventoryControl(){
 const [items,setItems]=useState<any[]>([]),[counts,setCounts]=useState<any[]>([]),[values,setValues]=useState<Record<number,string>>({}),[title,setTitle]=useState("شمارش پایان شیفت"),[msg,setMsg]=useState("");
 const load=()=>Promise.all([api<any[]>("/inventory-items/"),api<any[]>("/inventory-counts/")]).then(([i,c])=>{setItems(i);setCounts(c)});
 useEffect(()=>{load().catch(e=>setMsg(e.message))},[]);
 const create=async()=>{const lines=items.filter(x=>values[x.id]!==undefined&&values[x.id]!=="").map(x=>({item:x.id,counted_quantity:Number(values[x.id])}));if(!lines.length){setMsg("حداقل یک موجودی واقعی وارد کن");return}const c:any=await api("/inventory-counts/create/",{method:"POST",body:JSON.stringify({title,lines})});setValues({});setMsg(`✓ شمارش #${c.id} ساخته شد؛ برای ثبت اختلاف، «ثبت نهایی» را بزن.`);load()};
 const post=async(id:number)=>{try{await api(`/inventory-counts/${id}/post_count/`,{method:"POST",body:"{}"});setMsg("✓ مغایرت‌ها به Ledger انبار ثبت شدند");load()}catch(e:any){setMsg(e.message)}};
 return <div><h1 className="text-3xl font-black mb-2">شمارش فیزیکی انبار</h1><p className="text-[#8d8178] mb-5">موجودی واقعی با موجودی سیستم مقایسه و اختلاف فقط هنگام ثبت نهایی به Adjustment تبدیل می‌شود.</p>{msg&&<div className="card p-3 mb-4">{msg}</div>}
 <div className="card p-4 mb-5"><div className="flex gap-2 mb-3"><input className="border rounded-xl p-2 flex-1" value={title} onChange={e=>setTitle(e.target.value)}/><button className="btn btn-primary" onClick={create}>ساخت شمارش</button></div>
 <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-2">{items.map(x=><div className="border rounded-xl p-3" key={x.id}><div className="flex justify-between"><b>{x.name}</b><span className="text-sm">سیستم: {x.current_stock} {x.unit}</span></div><input className="border rounded-lg p-2 w-full mt-2" inputMode="decimal" placeholder="موجودی شمارش‌شده" value={values[x.id]??""} onChange={e=>setValues(v=>({...v,[x.id]:e.target.value}))}/></div>)}</div></div>
 <div className="space-y-3">{counts.map(c=><div className="card p-4" key={c.id}><div className="flex justify-between items-center"><div><b>{c.title}</b><div className="text-xs text-[#8d8178]">{c.status} — {new Date(c.created_at).toLocaleString("fa-IR")}</div></div>{c.status==="DRAFT"&&<button className="btn btn-primary" onClick={()=>post(c.id)}>ثبت نهایی و اعمال اختلاف</button>}</div>
 {c.lines?.length>0&&<div className="mt-3 grid md:grid-cols-3 gap-2 text-sm">{c.lines.map((l:any)=><div className="border-t pt-2" key={l.id}>{l.item_name}: سیستم {l.system_quantity} ← واقعی {l.counted_quantity} | اختلاف <b>{l.variance}</b> | ارزش {n(l.variance_value)}</div>)}</div>}</div>)}</div></div>
}

"use client";

import {useEffect,useRef,useState} from "react";
import {api} from "@/lib/api";

const money=(value:unknown)=>`${Number(value||0).toLocaleString("fa-IR")} ریال`;
export default function Reports(){
 const requestId=useRef(0);
 const [data,setData]=useState<any>(null),[branches,setBranches]=useState<any[]>([]),[branchId,setBranchId]=useState(""),[message,setMessage]=useState(""),[loading,setLoading]=useState(true);
 const load=async(branch:string)=>{
   const id=++requestId.current;
   setData(null);setMessage("");setLoading(true);
   if(!branch){setLoading(false);setMessage("شعبه‌ای انتخاب نشده است.");return;}
   try{const next=await api(`/reports/financial/?branch=${encodeURIComponent(branch)}`);if(id===requestId.current)setData(next);}
   catch(error:any){if(id===requestId.current){setData(null);setMessage(error.message||"دریافت گزارش مالی انجام نشد.");}}
   finally{if(id===requestId.current)setLoading(false);}
 };
 useEffect(()=>{
   let alive=true;
   api<any[]>("/branches/").then(nextBranches=>{
     if(!alive)return;
     setBranches(nextBranches);
     const stored=Number(localStorage.getItem("cafino_settings_branch")||0);
     const chosen=nextBranches.find(x=>x.id===stored&&x.is_active!==false)||
       (nextBranches.filter(x=>x.is_active!==false).length===1?nextBranches.find(x=>x.is_active!==false):null);
     if(chosen){setBranchId(String(chosen.id));void load(String(chosen.id));}
     else{setLoading(false);setMessage(nextBranches.length?"برای مشاهده گزارش، شعبه مجاز را انتخاب کنید.":"شعبه‌ای برای گزارش موجود نیست.");}
   }).catch(error=>{if(alive){setMessage(error.message||"دریافت شعب انجام نشد.");setLoading(false);}});
   return()=>{alive=false;requestId.current++};
 },[]);
 const cards=data?[{title:"درآمد خالص بدون مالیات",value:data.revenue,tone:"text-[#b9792d]"},{title:"بهای مواد مصرفی",value:data.cogs,tone:"text-red-700"},{title:"سود ناخالص",value:data.gross_profit,tone:"text-emerald-700"},{title:"هزینهٔ جاری",value:data.expenses,tone:"text-amber-700"},{title:"سربار ماهانه",value:data.monthly_overhead,tone:"text-[#2b1e16]"},{title:"سود خالص مدیریتی",value:data.net_profit,tone:Number(data.net_profit)<0?"text-red-700":"text-emerald-700"}]:[];
 return <div className="space-y-5"><header className="flex flex-col gap-3 rounded-[22px] border border-[#eadfd3] bg-[#fffdf9] p-5 shadow-sm sm:flex-row sm:items-end sm:justify-between"><div><p className="mb-1 text-sm font-bold text-[#b9792d]">گزارش‌های مدیریتی</p><h1 className="text-3xl font-black">سود و نقطهٔ سربه‌سر</h1><p className="mt-2 text-[#8d8178]">فروش، هزینهٔ متغیر، سربار و سود مدیریتی شعبه را در یک نما بررسی کنید.</p></div><label className="text-sm font-bold">شعبه<select className="btn mr-2 min-w-48" value={branchId} onChange={event=>{setBranchId(event.target.value);void load(event.target.value)}}>{branches.filter(branch=>branch.is_active!==false).map(branch=><option key={branch.id} value={branch.id}>{branch.name}</option>)}</select></label></header>{message&&<div role="alert" className="card border-r-4 border-r-[#b9792d] p-4">{message} {branchId&&<button className="btn mr-2" onClick={()=>void load(branchId)}>تلاش دوباره</button>}</div>}{loading?<div className="card p-6 text-[#8d8178]">در حال محاسبهٔ گزارش مالی…</div>:data&&<><section className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">{cards.map(card=><article className="card p-4" key={card.title}><div className="text-sm text-[#8d8178]">{card.title}</div><b className={`mt-2 block text-xl ${card.tone}`}>{money(card.value)}</b></article>)}</section><section className="grid gap-4 lg:grid-cols-3"><article className="card p-5"><div className="text-sm text-[#8d8178]">میانگین مبلغ سفارش</div><b className="mt-2 block text-xl">{money(data.average_order_value)}</b></article><article className="card p-5"><div className="text-sm text-[#8d8178]">سفارش لازم برای سربه‌سر</div><b className="mt-2 block text-xl">{data.break_even_orders==null?"قابل محاسبه نیست":`${Math.ceil(Number(data.break_even_orders)).toLocaleString("fa-IR")} سفارش`}</b></article><article className="card p-5"><div className="text-sm text-[#8d8178]">فروش لازم برای سربه‌سر</div><b className="mt-2 block text-xl">{data.break_even_revenue==null?"قابل محاسبه نیست":money(data.break_even_revenue)}</b></article></section><section className="rounded-[22px] border border-[#eadfd3] bg-[#211711] p-5 text-white"><div className="text-sm text-[#dfbd93]">حاشیهٔ مشارکت</div><b className="mt-2 block text-3xl">{money(data.contribution_margin)}</b><p className="mt-3 text-sm text-[#e9ddd1]">این گزارش مدیریتی است و جایگزین حسابداری دوبل یا گزارش قانونی نیست.</p></section></>}</div>;
}

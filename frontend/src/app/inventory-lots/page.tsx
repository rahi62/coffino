"use client";

import {useEffect,useState} from "react";
import {api} from "@/lib/api";
import {formatLocalizedDate} from "@/lib/calendar";

export default function Lots(){
 const [rows,setRows]=useState<any[]>([]),[msg,setMsg]=useState("");
 const load=()=>api<any[]>("/inventory-lots/").then(setRows);
 useEffect(()=>{load().catch(e=>setMsg(e.message))},[]);
 const block=async(x:any)=>{await api(`/inventory-lots/${x.id}/block/`,{method:"POST",body:JSON.stringify({is_blocked:!x.is_blocked})});load()};
 return <div><h1 className="mb-2 text-3xl font-black">سری ساخت، انقضا و گردش موجودی</h1><p className="mb-5 text-[#8d8178]">سری ساخت با تاریخ انقضای نزدیک‌تر زودتر مصرف می‌شود؛ سری ساخت مسدود وارد چرخه مصرف نمی‌شود.</p>{msg&&<div className="card mb-4 p-3">{msg}</div>}<div className="card overflow-x-auto"><table className="w-full min-w-[720px] text-sm"><thead className="bg-[#eee6dc]"><tr><th className="p-3">کالا</th><th>سری ساخت</th><th>مانده</th><th>بها</th><th>انقضا</th><th>روز مانده</th><th></th></tr></thead><tbody>{rows.map(x=><tr className="border-t" key={x.id}><td className="p-3 font-bold">{x.item_name}</td><td>{x.lot_number}</td><td>{x.quantity_remaining}</td><td>{Number(x.unit_cost).toLocaleString("fa-IR")}</td><td>{x.expires_at?formatLocalizedDate(x.expires_at):"—"}</td><td className={x.days_to_expiry!=null&&x.days_to_expiry<0?"font-bold text-red-700":x.days_to_expiry!=null&&x.days_to_expiry<=3?"font-bold text-amber-700":""}>{x.days_to_expiry??"—"}</td><td><button className="btn" onClick={()=>block(x)}>{x.is_blocked?"فعال‌سازی":"مسدودسازی"}</button></td></tr>)}</tbody></table></div></div>
}

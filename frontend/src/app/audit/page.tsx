"use client";

import {useEffect,useState} from "react";
import {api} from "@/lib/api";
import {formatLocalizedDate} from "@/lib/calendar";
import {label} from "@/lib/i18n";

export default function Audit(){
 const [rows,setRows]=useState<any[]>([]);
 useEffect(()=>{api<any[]>("/audit-logs/").then(setRows).catch(()=>{})},[]);
 return <div><h1 className="mb-2 text-3xl font-black">گزارش رویدادها</h1><p className="mb-5 text-[#8d8178]">ردپای غیرقابل‌ابهام عملیات حساس کاربران</p><div className="card overflow-x-auto"><table className="w-full min-w-[640px] text-sm"><thead className="bg-[#eee6dc]"><tr><th className="p-3">زمان</th><th>کاربر</th><th>عملیات</th><th>موجودیت</th><th>شرح</th></tr></thead><tbody>{rows.map(x=><tr className="border-t" key={x.id}><td className="p-3">{formatLocalizedDate(x.created_at,true)}</td><td>{x.actor_name||"-"}</td><td><span className="badge">{label(x.action)}</span></td><td>{x.entity_type} #{x.entity_id}</td><td>{x.description}</td></tr>)}</tbody></table></div></div>
}

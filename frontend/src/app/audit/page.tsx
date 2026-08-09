"use client";
import {useEffect,useState} from "react";import {api} from "@/lib/api";
export default function Audit(){const [rows,setRows]=useState<any[]>([]);useEffect(()=>{api<any[]>("/audit-logs/").then(setRows).catch(()=>{})},[]);
return <div><h1 className="text-3xl font-black mb-2">Audit Log</h1><p className="text-[#8d8178] mb-5">ردپای غیرقابل‌ابهام عملیات حساس کاربران</p>
<div className="card overflow-hidden"><table className="w-full text-sm"><thead className="bg-[#eee6dc]"><tr><th className="p-3">زمان</th><th>کاربر</th><th>عملیات</th><th>موجودیت</th><th>شرح</th></tr></thead><tbody>{rows.map(x=><tr className="border-t" key={x.id}><td className="p-3">{new Date(x.created_at).toLocaleString("fa-IR")}</td><td>{x.actor_name||"-"}</td><td><span className="badge">{x.action}</span></td><td>{x.entity_type} #{x.entity_id}</td><td>{x.description}</td></tr>)}</tbody></table></div></div>}

"use client";import {useEffect,useState} from "react";import {api} from "@/lib/api";import {label} from "@/lib/i18n";
const tableTones:Record<string,{card:string;badge:string}>={
 FREE:{card:"hover:border-emerald-200",badge:"table-status-free"},
 OCCUPIED:{card:"hover:border-[#d9ad74]",badge:"table-status-occupied"},
 RESERVED:{card:"hover:border-violet-200",badge:"table-status-reserved"},
};
function tableCardClass(status:string){return `card p-5 text-right transition-colors ${tableTones[status]?.card||""}`}
function tableBadgeClass(status:string){return `badge ${tableTones[status]?.badge||""}`}
export default function Tables(){const [rows,setRows]=useState<any[]>([]);const load=()=>api<any[]>("/tables/").then(setRows);useEffect(()=>{load().catch(()=>{})},[]);async function toggle(t:any){if(t.status==="FREE"||t.status==="RESERVED")await api(`/tables/${t.id}/open_session/`,{method:"POST",body:JSON.stringify({customer_count:2})});else await api(`/tables/${t.id}/close_session/`,{method:"POST"});load()}return <div><h1 className="text-3xl font-black mb-5">سالن و میزها</h1><div className="grid grid-cols-2 md:grid-cols-4 gap-4">{rows.map(t=><button onClick={()=>toggle(t)} className={tableCardClass(t.status)} key={t.id}><div className="text-2xl font-black">میز {t.number}</div><div className="mt-2"><span className={tableBadgeClass(t.status)}>{label(t.status)}</span></div><div className="text-sm text-[#8d8178] mt-3">ظرفیت {t.capacity} نفر</div></button>)}</div></div>}

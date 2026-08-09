"use client";
import {useEffect,useState} from "react";import {api} from "@/lib/api";
export default function Permissions(){
 const [users,setUsers]=useState<any[]>([]),[matrix,setMatrix]=useState<any>({groups:{},roles:[],role_permissions:{}}),[selected,setSelected]=useState<any>(null),[pin,setPin]=useState(""),[msg,setMsg]=useState("");
 const load=()=>Promise.all([api<any[]>("/users/"),api<any>("/permissions/matrix/")]).then(([u,m])=>{setUsers(u);setMatrix(m);if(!selected&&u[0])setSelected(u[0])});
 useEffect(()=>{load().catch(e=>setMsg(e.message))},[]);
 const inherited=(code:string)=>{const base=matrix.role_permissions?.[selected?.role]||[];return base.includes("*")||base.includes(code)}
 const setOverride=(code:string,value:string)=>{const o={...(selected.permission_overrides||{})};if(value==="inherit")delete o[code];else o[code]=value==="allow";setSelected({...selected,permission_overrides:o})}
 const save=async()=>{const u=await api<any>(`/users/${selected.id}/permissions/`,{method:"POST",body:JSON.stringify({overrides:selected.permission_overrides||{}})});setSelected(u);setMsg("✓ دسترسی‌ها ذخیره شد");load()};
 const role=async(v:string)=>{const u=await api<any>(`/users/${selected.id}/role/`,{method:"POST",body:JSON.stringify({role:v})});setSelected(u);load()};
 const savePin=async()=>{await api("/manager-pin/set/",{method:"POST",body:JSON.stringify({pin})});setPin("");setMsg("✓ PIN مدیریتی شما به‌روزرسانی شد")};
 return <div><h1 className="text-3xl font-black mb-2">Permission Matrix</h1><p className="text-[#8d8178] mb-5">دسترسی پایه نقش + Allow/Deny اختصاصی هر کاربر</p>{msg&&<div className="card p-3 mb-4">{msg}</div>}
 <div className="grid grid-cols-[280px_1fr] gap-5">
  <aside className="card p-3">{users.map(u=><button key={u.id} onClick={()=>setSelected(u)} className={`w-full text-right p-3 rounded-xl mb-2 ${selected?.id===u.id?"bg-[#eee6dc]":""}`}><b>{u.first_name||u.username}</b><div className="text-xs text-[#8d8178]">{u.role} — {u.branch_name||"بدون شعبه"}</div></button>)}</aside>
  {selected&&<section className="space-y-4"><div className="card p-4 flex items-center justify-between"><div><b>{selected.first_name||selected.username}</b><div className="text-xs text-[#8d8178]">نقش پایه</div></div><select className="btn" value={selected.role} onChange={e=>role(e.target.value)}>{matrix.roles.map((r:any)=><option key={r[0]} value={r[0]}>{r[1]}</option>)}</select></div>
  {Object.entries(matrix.groups||{}).map(([group,rows]:any)=><div className="card p-4" key={group}><h2 className="font-black text-lg mb-3">{group}</h2><div className="space-y-2">{rows.map((r:any)=>{const code=r[0],label=r[1],ov=selected.permission_overrides?.[code];return <div className="grid grid-cols-[1fr_180px_100px] items-center gap-2 border-t pt-2" key={code}><div><b>{label}</b><div className="text-xs text-[#8d8178]">{code}</div></div><select className="btn" value={ov===undefined?"inherit":ov?"allow":"deny"} onChange={e=>setOverride(code,e.target.value)}><option value="inherit">ارث‌بری از نقش</option><option value="allow">اجازه اختصاصی</option><option value="deny">ممنوع اختصاصی</option></select><span className="text-xs">{inherited(code)?"پایه: مجاز":"پایه: غیرمجاز"}</span></div>})}</div></div>)}
  <button className="btn btn-primary" onClick={save}>ذخیره Permissionها</button></section>}
 </div>
 <div className="card p-4 mt-5 max-w-xl"><h2 className="font-black text-lg">PIN Override مدیر</h2><p className="text-sm text-[#8d8178] my-2">PIN به‌صورت Hash ذخیره می‌شود و توکن Override فقط ۱۲۰ ثانیه اعتبار دارد.</p><div className="flex gap-2"><input type="password" inputMode="numeric" className="border rounded-xl p-2 flex-1" placeholder="PIN چهار تا هشت رقمی" value={pin} onChange={e=>setPin(e.target.value)}/><button className="btn btn-primary" onClick={savePin}>ثبت PIN من</button></div></div>
 </div>
}

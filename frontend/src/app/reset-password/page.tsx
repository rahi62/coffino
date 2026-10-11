"use client";
import Link from "next/link";
import {useEffect,useState} from "react";
import {Coffee,KeyRound} from "lucide-react";
import {resetPassword} from "@/lib/auth";

const grantKey="cafino_password_recovery_grant";

export default function ResetPasswordPage(){
 const [grant,setGrant]=useState("");const [password,setPassword]=useState("");const [confirmation,setConfirmation]=useState("");
 const [busy,setBusy]=useState(false);const [error,setError]=useState("");
 useEffect(()=>{setGrant(sessionStorage.getItem(grantKey)||"")},[]);
 const submit=async(e:React.FormEvent)=>{e.preventDefault();setError("");if(password!==confirmation){setError("تکرار گذرواژه یکسان نیست.");return}setBusy(true);try{await resetPassword(grant,password,confirmation);sessionStorage.removeItem(grantKey);location.assign("/login?reset=1")}catch(err:any){setError(err?.message||"تغییر گذرواژه انجام نشد.")}finally{setBusy(false)}};
 return <div className="fixed inset-0 z-50 overflow-y-auto bg-[#f4efe8] px-4 py-10"><div className="mx-auto max-w-md"><div className="mb-5 flex items-center gap-2 font-black"><span className="grid size-10 place-items-center rounded-xl bg-[#211711] text-white"><Coffee size={19}/></span>کافینو</div><section className="rounded-[26px] border border-[#e5ddd3] bg-[#fffdf9] p-6 shadow-xl shadow-[#211711]/5 sm:p-8">
  <div className="flex items-center gap-2"><KeyRound size={20} className="text-[#b9792d]"/><h1 className="text-2xl font-black">گذرواژه جدید</h1></div>
  {!grant?<div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-900">درخواست بازیابی معتبر در این مرورگر پیدا نشد. <Link href="/forgot-password" className="font-black underline">بازیابی را دوباره شروع کنید.</Link></div>:<form onSubmit={submit} className="mt-5 space-y-4">
   <label className="block text-sm font-bold">گذرواژه جدید<input autoFocus dir="ltr" type="password" autoComplete="new-password" value={password} onChange={e=>setPassword(e.target.value)} className="mt-2 h-12 w-full rounded-xl border border-[#e6ddd3] bg-[#faf7f2] px-4 text-left outline-none focus:border-[#b9792d]"/></label>
   <label className="block text-sm font-bold">تکرار گذرواژه<input dir="ltr" type="password" autoComplete="new-password" value={confirmation} onChange={e=>setConfirmation(e.target.value)} className="mt-2 h-12 w-full rounded-xl border border-[#e6ddd3] bg-[#faf7f2] px-4 text-left outline-none focus:border-[#b9792d]"/></label>
   <p className="text-xs leading-5 text-[#8d8178]">حداقل ۱۲ کاراکتر، شامل حرف لاتین و عدد.</p>
   {error&&<div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-800">{error}</div>}
   <button disabled={busy||password.length<12} className="h-12 w-full rounded-xl bg-[#211711] font-bold text-white disabled:opacity-50">{busy?"در حال ذخیره…":"تغییر گذرواژه"}</button>
  </form>}
 </section></div></div>;
}

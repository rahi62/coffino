"use client";
import Link from "next/link";
import {useState} from "react";
import {ArrowRight,Coffee,ShieldCheck} from "lucide-react";
import OtpForm from "@/components/otp-form";
import {requestPasswordRecovery,verifyPasswordRecoveryOtp} from "@/lib/auth";

const grantKey="cafino_password_recovery_grant";

export default function ForgotPasswordPage(){
 const [identifier,setIdentifier]=useState("");const [challengeId,setChallengeId]=useState("");
 const [retryAfter,setRetryAfter]=useState(0);const [resendVersion,setResendVersion]=useState(0);
 const [busy,setBusy]=useState(false);const [error,setError]=useState("");const [message,setMessage]=useState("");
 const run=async(fn:()=>Promise<void>)=>{if(busy)return;setBusy(true);setError("");try{await fn()}catch(e:any){setError(e?.message||"بازیابی انجام نشد.")}finally{setBusy(false)}};
 const request=()=>run(async()=>{const r=await requestPasswordRecovery(identifier.trim());setChallengeId(r.challenge_id);setRetryAfter(r.retry_after_seconds);setResendVersion(v=>v+1);setMessage(r.detail)});
 const verify=(code:string)=>run(async()=>{const r=await verifyPasswordRecoveryOtp(challengeId,code);sessionStorage.setItem(grantKey,r.verification_grant);location.assign("/reset-password")});
 return <AuthCard>
  <Link href="/login" className="mb-5 inline-flex items-center gap-1 text-sm font-bold text-[#8d8178]"><ArrowRight size={16}/> بازگشت به ورود</Link>
  <h1 className="text-2xl font-black">بازیابی گذرواژه</h1>
  {!challengeId?<div className="mt-5 space-y-4">
   <p className="text-sm leading-6 text-[#8d8178]">نام کاربری، ایمیل یا شماره همراه حساب را وارد کنید. برای امنیت، پاسخ وجود یا عدم وجود حساب را مشخص نمی‌کند.</p>
   <input autoFocus dir="ltr" value={identifier} onChange={e=>setIdentifier(e.target.value)} placeholder="username / email / 0912..." className="h-12 w-full rounded-xl border border-[#e6ddd3] bg-[#faf7f2] px-4 text-left outline-none focus:border-[#b9792d]"/>
   <button onClick={()=>void request()} disabled={busy||!identifier.trim()} className="h-12 w-full rounded-xl bg-[#211711] font-bold text-white disabled:opacity-50">{busy?"در حال بررسی…":"ادامه بازیابی"}</button>
  </div>:<div className="mt-5"><div className="mb-4 rounded-xl bg-[#f7f0e8] p-3 text-xs leading-6 text-[#75685f]">{message||"اگر حساب قابل بازیابی باشد، کد ارسال شده است."}</div><OtpForm busy={busy} retryAfterSeconds={retryAfter} resendVersion={resendVersion} onSubmit={verify} onResend={request} title="کد بازیابی" description="اگر برای این حساب کد پیامکی دریافت کرده‌اید، آن را وارد کنید."/></div>}
  {error&&<div className="mt-4 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-800">{error}</div>}
  <div className="mt-5 flex gap-2 text-xs text-[#8d8178]"><ShieldCheck size={16} className="shrink-0 text-[#b9792d]"/>کد بازیابی کوتاه‌عمر و یک‌بارمصرف است.</div>
 </AuthCard>
}

function AuthCard({children}:{children:React.ReactNode}){return <div className="fixed inset-0 z-50 overflow-y-auto bg-[#f4efe8] px-4 py-10"><div className="mx-auto max-w-md"><div className="mb-5 flex items-center gap-2 font-black"><span className="grid size-10 place-items-center rounded-xl bg-[#211711] text-white"><Coffee size={19}/></span>کافینو</div><section className="rounded-[26px] border border-[#e5ddd3] bg-[#fffdf9] p-6 shadow-xl shadow-[#211711]/5 sm:p-8">{children}</section></div></div>}

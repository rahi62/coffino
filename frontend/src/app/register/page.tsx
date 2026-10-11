"use client";
import Link from "next/link";
import {useMemo,useState} from "react";
import {Check,ChevronLeft,Coffee,ShieldCheck,Store,UserRound} from "lucide-react";
import OtpForm from "@/components/otp-form";
import {
  loginWithPassword,
  registerSaasOwner,
  requestRegistrationOtp,
  verifyRegistrationOtp,
} from "@/lib/auth";
import {canContinueRegistration,normalizeMobileInput} from "@/lib/registration-state.mjs";

const steps=["شماره همراه","تأیید","کسب‌وکار","حساب مالک","شعبه"];
const businessTypes=[
 ["CAFE","کافه"],["RESTAURANT","رستوران"],["FAST_FOOD","فست‌فود"],
 ["BAKERY","بیکری"],["PASTRY","قنادی"],["CATERING","کترینگ"],["HOTEL_RESTAURANT","رستوران هتل"],["OTHER","سایر"],
];

export default function RegisterPage(){
 const [step,setStep]=useState(0);
 const [busy,setBusy]=useState(false);
 const [error,setError]=useState("");
 const [mobile,setMobile]=useState("");
 const [challengeId,setChallengeId]=useState("");
 const [retryAfter,setRetryAfter]=useState(0);
 const [resendVersion,setResendVersion]=useState(0);
 const [verificationGrant,setVerificationGrant]=useState("");
 const [businessName,setBusinessName]=useState("");
 const [businessType,setBusinessType]=useState("CAFE");
 const [username,setUsername]=useState("");
 const [email,setEmail]=useState("");
 const [password,setPassword]=useState("");
 const [passwordConfirmation,setPasswordConfirmation]=useState("");
 const [branchName,setBranchName]=useState("شعبه اصلی");
 const [branchPhone,setBranchPhone]=useState("");
 const [copyMobile,setCopyMobile]=useState(true);

 const state=useMemo(()=>({
   mobile,verificationGrant,businessName,businessType,username,password,passwordConfirmation,branchName,
 }),[mobile,verificationGrant,businessName,businessType,username,password,passwordConfirmation,branchName]);

 const run=async(fn:()=>Promise<void>)=>{if(busy)return;setBusy(true);setError("");try{await fn()}catch(e:any){setError(e?.message||"انجام عملیات ممکن نشد.")}finally{setBusy(false)}};

 const sendOtp=()=>run(async()=>{
   const response=await requestRegistrationOtp(normalizeMobileInput(mobile));
   setChallengeId(response.challenge_id);setRetryAfter(response.retry_after_seconds);setResendVersion(x=>x+1);setStep(1);
 });
 const verifyOtp=(code:string)=>run(async()=>{
   const response=await verifyRegistrationOtp(challengeId,code);
   setVerificationGrant(response.verification_grant);setStep(2);
 });
 const finish=()=>run(async()=>{
   await registerSaasOwner({
     business_name:businessName.trim(),business_type:businessType,
     branch_name:branchName.trim(),branch_phone:branchPhone.trim(),
     copy_owner_mobile_to_branch:copyMobile,
     username:username.trim(),email:email.trim(),password,
     password_confirmation:passwordConfirmation,verification_grant:verificationGrant,
   });
   try{
     await loginWithPassword(username.trim(),password);
     location.assign("/settings/onboarding");
   }catch{
     // Registration is already committed. Never retry tenant creation with a consumed grant.
     location.assign("/login?registered=1");
   }
 });

 const continueStep=()=>{
   const key=["mobile","verify","business","owner","branch"][step];
   if(!canContinueRegistration(key,state)){setError("اطلاعات این مرحله را کامل و صحیح وارد کنید.");return}
   setError("");
   if(step===0){void sendOtp();return}
   if(step===4){void finish();return}
   setStep(x=>x+1);
 };

 return <div className="fixed inset-0 z-50 overflow-y-auto bg-[#f4efe8] px-4 py-7 sm:px-6">
  <div className="mx-auto max-w-3xl">
   <header className="mb-5 flex items-center justify-between gap-3">
    <Link href="/login" className="flex items-center gap-2 font-black text-[#211711]"><span className="grid size-10 place-items-center rounded-xl bg-[#211711] text-white"><Coffee size={19}/></span>کافینو</Link>
    <Link href="/login" className="text-sm font-bold text-[#8d8178]">حساب دارید؟ ورود</Link>
   </header>

   <section className="overflow-hidden rounded-[28px] border border-[#e5ddd3] bg-[#fffdf9] shadow-xl shadow-[#211711]/5">
    <div className="border-b border-[#eee6dc] p-5 sm:p-7">
      <span className="text-xs font-black text-[#b9792d]">راه‌اندازی SaaS</span>
      <h1 className="mt-1 text-2xl font-black text-[#211711] sm:text-3xl">کسب‌وکارتان را در کافینو بسازید</h1>
      <p className="mt-2 text-sm leading-6 text-[#8d8178]">ابتدا مالک حساب را تأیید می‌کنیم؛ سپس مجموعه و شعبه اصلی ساخته می‌شود.</p>
      <div className="mt-5 grid grid-cols-5 gap-1.5">
       {steps.map((label,index)=><div key={label} className="min-w-0">
        <div className={`h-1.5 rounded-full ${index<=step?"bg-[#b9792d]":"bg-[#e9dfd3]"}`}/>
        <div className={`mt-1 hidden truncate text-[10px] sm:block ${index===step?"font-bold text-[#211711]":"text-[#9c9189]"}`}>{label}</div>
       </div>)}
      </div>
    </div>

    <div className="p-5 sm:p-7">
     {step===0&&<div className="space-y-4">
      <div className="flex items-center gap-2"><ShieldCheck size={21} className="text-[#b9792d]"/><h2 className="text-lg font-black">شماره همراه مالک</h2></div>
      <p className="text-sm leading-6 text-[#8d8178]">این شماره برای امنیت حساب، ورود با کد و بازیابی استفاده می‌شود.</p>
      <label className="block text-sm font-bold">شماره همراه
       <input dir="ltr" inputMode="tel" autoFocus value={mobile} onChange={e=>{setMobile(e.target.value);setError("")}} placeholder="09123456789" className="mt-2 h-12 w-full rounded-xl border border-[#e6ddd3] bg-[#faf7f2] px-4 text-left outline-none focus:border-[#b9792d]"/>
      </label>
     </div>}

     {step===1&&<OtpForm busy={busy} retryAfterSeconds={retryAfter} resendVersion={resendVersion} onSubmit={verifyOtp} onResend={sendOtp} description={`کد تأیید برای ${mobile} درخواست شده است.`}/>}

     {step===1&&<button type="button" disabled={busy} className="mt-4 text-sm font-bold text-[#a46722] disabled:opacity-50" onClick={()=>{setChallengeId("");setVerificationGrant("");setRetryAfter(0);setStep(0)}}>اصلاح شماره همراه</button>}
     {step===2&&<div className="space-y-4">
      <div className="flex items-center gap-2"><Store size={21} className="text-[#b9792d]"/><h2 className="text-lg font-black">مشخصات کسب‌وکار</h2></div>
      <label className="block text-sm font-bold">نام مجموعه<input autoFocus value={businessName} onChange={e=>setBusinessName(e.target.value)} placeholder="مثلاً کافه مرکزی" className="mt-2 h-12 w-full rounded-xl border border-[#e6ddd3] bg-[#faf7f2] px-4 outline-none focus:border-[#b9792d]"/></label>
      <label className="block text-sm font-bold">نوع مجموعه<select value={businessType} onChange={e=>setBusinessType(e.target.value)} className="mt-2 h-12 w-full rounded-xl border border-[#e6ddd3] bg-[#faf7f2] px-3 outline-none focus:border-[#b9792d]">{businessTypes.map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></label>
     </div>}

     {step===3&&<div className="space-y-4">
      <div className="flex items-center gap-2"><UserRound size={21} className="text-[#b9792d]"/><h2 className="text-lg font-black">حساب مالک</h2></div>
      <label className="block text-sm font-bold">نام کاربری<input dir="ltr" autoFocus value={username} onChange={e=>setUsername(e.target.value)} className="mt-2 h-12 w-full rounded-xl border border-[#e6ddd3] bg-[#faf7f2] px-4 text-left outline-none focus:border-[#b9792d]"/></label>
      <label className="block text-sm font-bold">ایمیل <span className="font-normal text-[#9b9087]">(اختیاری)</span><input dir="ltr" type="email" value={email} onChange={e=>setEmail(e.target.value)} className="mt-2 h-12 w-full rounded-xl border border-[#e6ddd3] bg-[#faf7f2] px-4 text-left outline-none focus:border-[#b9792d]"/></label>
      <div className="grid gap-3 sm:grid-cols-2">
       <label className="block text-sm font-bold">گذرواژه<input dir="ltr" type="password" autoComplete="new-password" value={password} onChange={e=>setPassword(e.target.value)} className="mt-2 h-12 w-full rounded-xl border border-[#e6ddd3] bg-[#faf7f2] px-4 text-left outline-none focus:border-[#b9792d]"/></label>
       <label className="block text-sm font-bold">تکرار گذرواژه<input dir="ltr" type="password" autoComplete="new-password" value={passwordConfirmation} onChange={e=>setPasswordConfirmation(e.target.value)} className="mt-2 h-12 w-full rounded-xl border border-[#e6ddd3] bg-[#faf7f2] px-4 text-left outline-none focus:border-[#b9792d]"/></label>
      </div>
      <p className="text-xs leading-5 text-[#8d8178]">حداقل ۱۲ کاراکتر، شامل حرف لاتین و عدد؛ نام کاربری یا نام مجموعه در آن نباشد.</p>
     </div>}

     {step===4&&<div className="space-y-4">
      <div className="flex items-center gap-2"><Store size={21} className="text-[#b9792d]"/><h2 className="text-lg font-black">شعبه اصلی</h2></div>
      <label className="block text-sm font-bold">نام شعبه<input autoFocus value={branchName} onChange={e=>setBranchName(e.target.value)} className="mt-2 h-12 w-full rounded-xl border border-[#e6ddd3] bg-[#faf7f2] px-4 outline-none focus:border-[#b9792d]"/></label>
      {!copyMobile&&<label className="block text-sm font-bold">تلفن شعبه<input dir="ltr" value={branchPhone} onChange={e=>setBranchPhone(e.target.value)} className="mt-2 h-12 w-full rounded-xl border border-[#e6ddd3] bg-[#faf7f2] px-4 text-left outline-none focus:border-[#b9792d]"/></label>}
      <label className="flex items-start gap-3 rounded-xl border border-[#e6ddd3] bg-[#faf7f2] p-3 text-sm"><input type="checkbox" checked={copyMobile} onChange={e=>setCopyMobile(e.target.checked)} className="mt-1"/><span><b>شماره مالک به‌عنوان تلفن شعبه ثبت شود</b><span className="mt-1 block text-xs text-[#8d8178]">بعداً از تنظیمات شعبه قابل تغییر است.</span></span></label>
      <div className="rounded-xl bg-emerald-50 p-3 text-sm text-emerald-900"><Check size={17} className="ml-1 inline"/>پس از ساخت حساب، مستقیم وارد راه‌اندازی هوشمند مجموعه می‌شوید.</div>
     </div>}

     {error&&<div role="alert" className="mt-4 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-800">{error}</div>}

     {step!==1&&<div className="mt-6 flex items-center justify-between gap-3">
      <button type="button" disabled={busy||step===0} onClick={()=>{setError("");setStep(x=>Math.max(0,x-1))}} className="flex h-11 items-center gap-1 rounded-xl px-3 text-sm font-bold text-[#75685f] disabled:invisible"><ChevronLeft size={17}/> قبلی</button>
      <button type="button" disabled={busy} onClick={continueStep} className="h-11 rounded-xl bg-[#211711] px-6 text-sm font-bold text-white disabled:opacity-50">{busy?"در حال انجام…":step===4?"ساخت حساب و ورود":"مرحله بعد"}</button>
     </div>}
    </div>
   </section>
  </div>
 </div>;
}

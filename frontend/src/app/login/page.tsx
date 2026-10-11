"use client";
import Link from "next/link";
import {useEffect,useState} from "react";
import {Coffee,Eye,EyeOff,KeyRound,ShieldCheck,UserRound} from "lucide-react";
import OtpForm from "@/components/otp-form";
import {localBootstrap,localBootstrapStatus} from "@/lib/api";
import {loginWithOtp,loginWithPassword,requestLoginOtp} from "@/lib/auth";

type PageMode="checking"|"login"|"setup";
type LoginMethod="password"|"otp";

export default function Login(){
 const [mode,setMode]=useState<PageMode>("checking");
 const [method,setMethod]=useState<LoginMethod>("password");
 const [notice,setNotice]=useState("");
 const [busy,setBusy]=useState(false);const [error,setError]=useState("");
 const [username,setUsername]=useState("");const [password,setPassword]=useState("");const [showPassword,setShowPassword]=useState(false);
 const [mobile,setMobile]=useState("");const [challengeId,setChallengeId]=useState("");
 const [businessName,setBusinessName]=useState("");const [branchName,setBranchName]=useState("شعبه اصلی");const [businessType,setBusinessType]=useState("CAFE");
 const [ownerUsername,setOwnerUsername]=useState("owner");const [ownerEmail,setOwnerEmail]=useState("");const [ownerPassword,setOwnerPassword]=useState("");const [ownerPasswordConfirmation,setOwnerPasswordConfirmation]=useState("");

 useEffect(()=>{
   const params=new URLSearchParams(location.search);
   if(params.get("registered")==="1")setNotice("حساب کسب‌وکار با موفقیت ساخته شد. برای ادامه وارد شوید.");
   else if(params.get("reset")==="1")setNotice("گذرواژه با موفقیت تغییر کرد. با گذرواژه جدید وارد شوید.");
 },[]);

 useEffect(()=>{let cancelled=false;const sleep=(ms:number)=>new Promise(r=>setTimeout(r,ms));(async()=>{
   const attempts=typeof window!=="undefined"&&Boolean((window as any).cafino)?60:1;
   for(let i=0;i<attempts;i++)try{
     const s=await localBootstrapStatus();if(cancelled)return;
     setMode(s?.available&&s.needs_setup?"setup":"login");return;
   }catch{if(i<attempts-1)await sleep(500);else if(!cancelled)setMode("login")}
 })();return()=>{cancelled=true}},[]);

 const run=async(fn:()=>Promise<void>)=>{setBusy(true);setError("");try{await fn()}catch(e:any){setError(e?.message||"ورود انجام نشد.")}finally{setBusy(false)}};
 const passwordSubmit=(e:React.FormEvent)=>{e.preventDefault();void run(async()=>{await loginWithPassword(username.trim(),password);location.assign("/")})};
 const otpRequest=()=>run(async()=>{const x=await requestLoginOtp(mobile);setChallengeId(x.challenge_id)});
 const otpVerify=(code:string)=>run(async()=>{await loginWithOtp(challengeId,code);location.assign("/")});
 const setupSubmit=(e:React.FormEvent)=>{e.preventDefault();void run(async()=>{
   if(ownerPassword!==ownerPasswordConfirmation)throw new Error("تکرار گذرواژه یکسان نیست.");
   await localBootstrap({business_name:businessName.trim(),branch_name:branchName.trim(),business_type:businessType,username:ownerUsername.trim(),email:ownerEmail.trim(),password:ownerPassword,password_confirmation:ownerPasswordConfirmation});
   await loginWithPassword(ownerUsername.trim(),ownerPassword);location.assign("/");
 })};

 return <div className="fixed inset-0 z-50 flex min-h-screen overflow-hidden bg-[#f0ece6]">
  <section className="flex w-full items-center justify-center overflow-y-auto bg-[#fffdf9] px-6 py-10 sm:px-10 lg:w-[48%] lg:min-w-[430px] lg:px-14">
   <div className="w-full max-w-[380px]">
    <div className="mb-8 flex items-center gap-3"><span className="grid size-11 place-items-center rounded-2xl bg-[#211711] text-white"><Coffee size={21}/></span><div><p className="text-lg font-black">کافینو</p><p className="text-xs text-[#8d8178]">مدیریت هوشمند پذیرایی</p></div></div>

    {mode==="checking"&&<div className="rounded-3xl border border-[#e6ddd3] bg-white p-6"><div className="mb-3 size-8 animate-pulse rounded-xl bg-[#b9792d]/20"/><b>در حال بررسی وضعیت ورود…</b></div>}

    {mode==="login"&&<div>
     <h1 className="text-3xl font-black text-[#211711]">خوش آمدید</h1><p className="mt-2 text-sm text-[#8d8178]">با گذرواژه یا کد یک‌بارمصرف وارد پنل شوید.</p>
     {notice&&<div role="status" className="mt-5 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm leading-6 text-emerald-900">{notice}</div>}
     <div className="mt-6 grid grid-cols-2 rounded-xl bg-[#f2ece5] p-1">
      <button onClick={()=>{setMethod("password");setChallengeId("");setError("")}} className={`rounded-lg px-3 py-2 text-sm font-bold ${method==="password"?"bg-white shadow-sm":"text-[#82756c]"}`}><UserRound size={16} className="ml-1 inline"/>گذرواژه</button>
      <button onClick={()=>{setMethod("otp");setError("")}} className={`rounded-lg px-3 py-2 text-sm font-bold ${method==="otp"?"bg-white shadow-sm":"text-[#82756c]"}`}><KeyRound size={16} className="ml-1 inline"/>کد ورود</button>
     </div>

     {method==="password"?<form onSubmit={passwordSubmit} className="mt-5 space-y-4">
      <label className="block text-sm font-bold">نام کاربری<input autoFocus dir="ltr" autoComplete="username" value={username} onChange={e=>setUsername(e.target.value)} className="mt-2 h-12 w-full rounded-xl border border-[#e6ddd3] bg-[#faf7f2] px-4 text-left outline-none focus:border-[#b9792d]"/></label>
      <label className="block text-sm font-bold">گذرواژه<span className="relative mt-2 block"><input dir="ltr" autoComplete="current-password" type={showPassword?"text":"password"} value={password} onChange={e=>setPassword(e.target.value)} className="h-12 w-full rounded-xl border border-[#e6ddd3] bg-[#faf7f2] py-0 pl-12 pr-4 text-left outline-none focus:border-[#b9792d]"/><button type="button" onClick={()=>setShowPassword(x=>!x)} className="absolute left-2 top-1/2 grid size-9 -translate-y-1/2 place-items-center text-[#8d8178]" aria-label="نمایش یا پنهان کردن گذرواژه">{showPassword?<EyeOff size={18}/>:<Eye size={18}/>}</button></span></label>
      <div className="flex justify-end"><Link href="/forgot-password" className="text-sm font-bold text-[#a46722]">گذرواژه را فراموش کرده‌ام</Link></div>
      <button disabled={busy||!username.trim()||!password} className="h-12 w-full rounded-xl bg-[#211711] font-bold text-white disabled:opacity-50">{busy?"در حال ورود…":"ورود به پنل"}</button>
     </form>:<div className="mt-5">
      {!challengeId?<div className="space-y-4"><label className="block text-sm font-bold">شماره همراه تأییدشده<input autoFocus dir="ltr" inputMode="tel" value={mobile} onChange={e=>setMobile(e.target.value)} placeholder="09123456789" className="mt-2 h-12 w-full rounded-xl border border-[#e6ddd3] bg-[#faf7f2] px-4 text-left outline-none focus:border-[#b9792d]"/></label><button onClick={()=>void otpRequest()} disabled={busy||!mobile.trim()} className="h-12 w-full rounded-xl bg-[#211711] font-bold text-white disabled:opacity-50">{busy?"در حال ارسال…":"ارسال کد ورود"}</button></div>:<OtpForm busy={busy} onSubmit={otpVerify} onResend={otpRequest} title="کد ورود"/>}
     </div>}

     {error&&<div className="mt-4 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-800">{error}</div>}
     <div className="mt-6 border-t border-[#eee6dc] pt-5 text-center text-sm text-[#8d8178]">هنوز حساب ندارید؟ <Link href="/register" className="font-black text-[#a46722]">ایجاد حساب کسب‌وکار</Link></div>
     <div className="mt-4 flex items-center gap-2 text-xs text-[#8d8178]"><ShieldCheck size={16} className="text-[#b9792d]"/>دسترسی‌ها بر اساس کسب‌وکار، نقش و شعبه کنترل می‌شوند.</div>
    </div>}

    {mode==="setup"&&<form onSubmit={setupSubmit} className="space-y-3">
      <div className="mb-5"><span className="rounded-full bg-[#f6eadb] px-3 py-1 text-xs font-black text-[#a46722]">راه‌اندازی اولیه Local</span><h1 className="mt-3 text-2xl font-black">نصب محلی را آماده کنید</h1><p className="mt-2 text-sm text-[#8d8178]">فقط برای دیتابیس تازه Local فعال است.</p></div>
      <input autoFocus placeholder="نام کسب‌وکار" value={businessName} onChange={e=>setBusinessName(e.target.value)} className="h-11 w-full rounded-xl border px-3"/>
      <div className="grid grid-cols-2 gap-2"><input placeholder="شعبه اصلی" value={branchName} onChange={e=>setBranchName(e.target.value)} className="h-11 rounded-xl border px-3"/><select value={businessType} onChange={e=>setBusinessType(e.target.value)} className="h-11 rounded-xl border px-2"><option value="CAFE">کافه</option><option value="RESTAURANT">رستوران</option><option value="FAST_FOOD">فست‌فود</option><option value="BAKERY">بیکری</option></select></div>
      <input dir="ltr" placeholder="نام کاربری مالک" value={ownerUsername} onChange={e=>setOwnerUsername(e.target.value)} className="h-11 w-full rounded-xl border px-3 text-left"/>
      <input dir="ltr" type="email" placeholder="ایمیل (اختیاری)" value={ownerEmail} onChange={e=>setOwnerEmail(e.target.value)} className="h-11 w-full rounded-xl border px-3 text-left"/>
      <input dir="ltr" type="password" placeholder="گذرواژه مالک" value={ownerPassword} onChange={e=>setOwnerPassword(e.target.value)} className="h-11 w-full rounded-xl border px-3 text-left"/>
      <input dir="ltr" type="password" placeholder="تکرار گذرواژه" value={ownerPasswordConfirmation} onChange={e=>setOwnerPasswordConfirmation(e.target.value)} className="h-11 w-full rounded-xl border px-3 text-left"/>
      {error&&<div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-800">{error}</div>}
      <button disabled={busy} className="h-12 w-full rounded-xl bg-[#211711] font-bold text-white disabled:opacity-50">{busy?"در حال ساخت…":"ساخت نصب محلی و ورود"}</button>
    </form>}
   </div>
  </section>
  <aside className="relative hidden flex-1 overflow-hidden bg-[#211711] p-10 text-white lg:flex lg:items-center">
   <div className="absolute inset-0 opacity-20" style={{backgroundImage:"radial-gradient(circle, #fff 1px, transparent 1px)",backgroundSize:"24px 24px"}}/>
   <div className="relative mx-auto max-w-xl"><span className="rounded-full bg-white/10 px-3 py-1 text-xs font-bold text-[#dfbd93]">Hospitality OS</span><h2 className="mt-5 text-5xl font-black leading-[1.25]">فروش، سالن، آشپزخانه و مدیریت؛ یکپارچه.</h2><p className="mt-5 max-w-lg text-base leading-8 text-white/65">کافینو عملیات روزانه کافه و رستوران را از سفارش تا انبار و گزارش در یک محیط واحد نگه می‌دارد.</p><div className="mt-8 grid grid-cols-3 gap-3">{["POS و سفارش","انبار و خرید","گزارش مدیریتی"].map(x=><div key={x} className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm font-bold">{x}</div>)}</div></div>
  </aside>
 </div>;
}

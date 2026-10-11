"use client";
import {useEffect,useState} from "react";
import {KeyRound,RotateCcw} from "lucide-react";
import {asciiDigits} from "@/lib/registration-state.mjs";

export default function OtpForm({
  title="کد تأیید",
  description="کد شش‌رقمی ارسال‌شده را وارد کنید.",
  busy=false,
  onSubmit,
  onResend,
  retryAfterSeconds=0,
  resendVersion=0,
}:{title?:string;description?:string;busy?:boolean;onSubmit:(code:string)=>Promise<void>|void;onResend?:()=>Promise<void>|void;retryAfterSeconds?:number;resendVersion?:number}){
  const [code,setCode]=useState("");
  const [remaining,setRemaining]=useState(0);
  useEffect(()=>{setRemaining(Math.max(0,Math.ceil(retryAfterSeconds)))},[retryAfterSeconds,resendVersion]);
  useEffect(()=>{if(remaining<=0)return;const timer=window.setTimeout(()=>setRemaining(x=>Math.max(0,x-1)),1000);return()=>window.clearTimeout(timer)},[remaining]);
  const submit=async(e:React.FormEvent)=>{
    e.preventDefault();
    const normalized=asciiDigits(code).replace(/\D/g,"").slice(0,6);
    if(normalized.length!==6)return;
    await onSubmit(normalized);
  };
  return <form onSubmit={submit} className="space-y-4">
    <div>
      <div className="flex items-center gap-2"><KeyRound size={19}/><h2 className="font-black">{title}</h2></div>
      <p className="mt-1 text-sm leading-6 text-[#8d8178]">{description}</p>
    </div>
    <input
      autoFocus inputMode="numeric" autoComplete="one-time-code" dir="ltr"
      value={code}
      onChange={e=>setCode(asciiDigits(e.target.value).replace(/\D/g,"").slice(0,6))}
      placeholder="------"
      className="h-14 w-full rounded-xl border border-[#e6ddd3] bg-[#faf7f2] px-4 text-center font-mono text-2xl tracking-[.45em] outline-none focus:border-[#b9792d] focus:bg-white"
    />
    <button type="submit" disabled={busy||code.length!==6} className="h-12 w-full rounded-xl bg-[#211711] font-bold text-white disabled:opacity-50">
      {busy?"در حال بررسی…":"تأیید کد"}
    </button>
    {onResend&&<button type="button" disabled={busy||remaining>0} onClick={()=>void onResend()} className="mx-auto flex items-center gap-1 text-sm font-bold text-[#a46722] disabled:opacity-50">
      <RotateCcw size={15}/> {remaining>0?`ارسال مجدد تا ${remaining.toLocaleString("fa-IR")} ثانیه دیگر`:"ارسال مجدد کد"}
    </button>}
  </form>;
}

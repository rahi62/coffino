"use client";
import {useEffect,useState} from "react";
import {usePathname} from "next/navigation";
import {api} from "@/lib/api";
import {clearSession,hasStoredSession} from "@/lib/auth";

type AuthState="checking"|"ready"|"error";
const publicRoutes=["/login","/register","/forgot-password","/reset-password"];

function isPublic(pathname:string){
 return publicRoutes.includes(pathname)||pathname.startsWith("/menu/");
}

export default function AuthGuard({children}:{children:React.ReactNode}){
 const pathname=usePathname();
 const [state,setState]=useState<AuthState>("checking");

 useEffect(()=>{
  if(isPublic(pathname)){setState("ready");return}
  if(!hasStoredSession()){location.replace("/login");return}

  let cancelled=false;
  setState("checking");
  api("/me/").then(()=>{
   if(!cancelled)setState("ready");
  }).catch((error)=>{
   if(cancelled)return;
   const message=String(error?.message||"");
   if(message.includes("نشست")||!hasStoredSession()){
    clearSession();location.replace("/login");return;
   }
   setState("error");
  });
  return()=>{cancelled=true};
 },[pathname]);

 if(state==="ready")return <>{children}</>;
 if(state==="error")return <div className="p-10">
  <div className="mx-auto max-w-md rounded-2xl border border-red-200 bg-red-50 p-5 text-right text-red-900">
   <h1 className="font-black">ارتباط با سرور برقرار نشد</h1>
   <p className="mt-2 text-sm leading-6">اعتبار ورود قابل بررسی نیست. اتصال Backend را بررسی و دوباره تلاش کنید.</p>
   <button className="mt-4 rounded-xl bg-[#211711] px-4 py-2 text-sm font-bold text-white" onClick={()=>location.reload()}>تلاش دوباره</button>
  </div>
 </div>;
 return <div className="p-10">در حال بررسی ورود...</div>;
}

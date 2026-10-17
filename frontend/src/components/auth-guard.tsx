"use client";
import {useEffect,useState} from "react";
import {usePathname} from "next/navigation";
import {api} from "@/lib/api";
import {clearSession,getAccessToken,hasStoredSession} from "@/lib/auth";
import {isPublicRoute} from "@/lib/public-routes.mjs";

type AuthState="checking"|"ready"|"error";
// A full browser reload still validates with /me/. Internal remounts share a
// single verified access token so route changes do not flash the login screen.
let verifiedToken:string|null=null;
let verification:Promise<void>|null=null;
let verifyingToken:string|null=null;
function verifySession(token:string){
 if(verifiedToken===token)return Promise.resolve();
 if(verification&&verifyingToken===token)return verification;
 verifyingToken=token;
 const task=api("/me/").then(()=>{if(verifyingToken===token)verifiedToken=token;});
 verification=task.finally(()=>{if(verification===task)verification=null;});
 // Clear the promise on either resolution or rejection.
 const current=verification;
 void current.finally(()=>{if(verification===current){verification=null;verifyingToken=null;}}).catch(()=>{});
 return current;
}
export default function AuthGuard({children}:{children:React.ReactNode}){
 const pathname=usePathname();
 const publicRoute=isPublicRoute(pathname);
 const token=getAccessToken();
 const [state,setState]=useState<AuthState>(()=>publicRoute||Boolean(token&&verifiedToken===token)?"ready":"checking");

 useEffect(()=>{
  if(publicRoute){setState("ready");return;}
  if(!hasStoredSession()){verifiedToken=null;location.replace("/login");return;}
  const currentToken=getAccessToken();
  if(currentToken&&verifiedToken===currentToken){setState("ready");return;}
  let cancelled=false;
  setState("checking");
  verifySession(currentToken||"refresh-only").then(()=>{
   if(!cancelled)setState("ready");
  }).catch((error)=>{
   if(cancelled)return;
   const message=String(error?.message||"");
   verifiedToken=null;
   if(message.includes("نشست")||!hasStoredSession()){
    clearSession();location.replace("/login");return;
   }
   setState("error");
  });
  return()=>{cancelled=true};
 },[publicRoute,token]);

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

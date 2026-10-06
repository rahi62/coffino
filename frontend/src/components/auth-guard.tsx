"use client";
import {useEffect,useState} from "react";
import {usePathname} from "next/navigation";
import {base,clearToken,getToken} from "@/lib/api";

type AuthState="checking"|"ready"|"error";

export default function AuthGuard({children}:{children:React.ReactNode}){
 const pathname=usePathname();
 const [state,setState]=useState<AuthState>("checking");

 useEffect(()=>{
  const publicRoute=pathname==="/login"||pathname.startsWith("/menu/");
  if(publicRoute){setState("ready");return}

  const token=getToken();
  if(!token){location.replace("/login");return}

  const controller=new AbortController();
  setState("checking");

  fetch(`${base}/me/`,{
   headers:{Authorization:`Bearer ${token}`},
   cache:"no-store",
   signal:controller.signal,
  }).then(response=>{
   if(response.status===401){
    clearToken();
    location.replace("/login");
    return;
   }
   if(!response.ok)throw new Error(`session_check_${response.status}`);
   setState("ready");
  }).catch(error=>{
   if(error?.name==="AbortError")return;
   setState("error");
  });

  return()=>controller.abort();
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

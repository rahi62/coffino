"use client";
import {useEffect,useState} from "react";

declare global{interface Window{cafino?:{health:()=>Promise<any>;createBackup:()=>Promise<any>;restoreBackup:()=>Promise<any>}}}
export default function LocalTools(){
 const [health,setسلامت]=useState<any>(null),[msg,setMsg]=useState("");
 useEffect(()=>{window.cafino?.health().then(setسلامت).catch(()=>{})},[]);
 async function backup(){if(!window.cafino){setMsg("این قابلیت فقط در نسخه Electron فعال است");return}const r=await window.cafino.createBackup();setMsg(r.ok?`بکاپ ذخیره شد: ${r.path}`:r.canceled?"لغو شد":`خطا: ${r.error||"نامشخص"}`)}
 async function restore(){if(!window.cafino){setMsg("این قابلیت فقط در نسخه Electron فعال است");return}if(!confirm("دیتابیس فعلی با بکاپ انتخابی جایگزین شود؟"))return;const r=await window.cafino.restoreBackup();setMsg(r.ok?"بازیابی انجام شد.":r.canceled?"لغو شد":`خطا: ${r.error||"نامشخص"}`)}
 return <div><h1 className="text-3xl font-black mb-5">ابزارهای نسخه محلی</h1><div className="grid md:grid-cols-2 gap-4"><div className="card p-5"><h2 className="font-black text-xl mb-3">وضعیت Electron</h2><pre className="text-sm bg-[#f3ede5] p-3 rounded-xl overflow-auto">{JSON.stringify(health||{electron:false},null,2)}</pre></div><div className="card p-5"><h2 className="font-black text-xl mb-3">پشتیبان‌گیری</h2><p className="text-sm text-[#8d8178] leading-7 mb-4">بکاپ نسخه محلی مستقل از فضای ابری است و پایگاه داده محلی مجموعه را ذخیره یا بازیابی می‌کند.</p><div className="flex gap-2"><button className="btn btn-primary" onClick={backup}>ساخت بکاپ</button><button className="btn" onClick={restore}>بازیابی بکاپ</button></div>{msg&&<div className="mt-4 text-sm">{msg}</div>}</div></div></div>}

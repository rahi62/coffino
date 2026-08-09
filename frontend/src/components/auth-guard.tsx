"use client";
import {useEffect,useState} from "react";import {getToken} from "@/lib/api";
export default function AuthGuard({children}:{children:React.ReactNode}){const [ok,setOk]=useState(false);useEffect(()=>{if(location.pathname==="/login"||location.pathname.startsWith("/menu/")){setOk(true);return}if(!getToken()){location.href="/login";return}setOk(true)},[]);return ok?<>{children}</>:<div className="p-10">در حال بررسی ورود...</div>}

import {t, userMessage} from "@/lib/i18n";
import {
  ACCESS_TOKEN_KEY,
  REFRESH_TOKEN_KEY,
  clearSessionStorage,
  createRefreshCoordinator,
  readSession,
  writeSession,
} from "./auth-session.mjs";

export type TokenPair={access:string;refresh?:string};
export type OtpRequestResponse={
  detail:string;
  challenge_id:string;
  expires_at:string;
  retry_after_seconds:number;
  mobile?:string;
};

export const apiRoot=(process.env.NEXT_PUBLIC_API_ROOT||"").replace(/\/$/,"");
export const apiBase=(process.env.NEXT_PUBLIC_API_URL||`${apiRoot}/api/v1`).replace(/\/$/,"");

function browserStorage(){
  return typeof window==="undefined"?null:window.localStorage;
}

const storageAdapter={
  getItem(key:string){return browserStorage()?.getItem(key)??null},
  setItem(key:string,value:string){browserStorage()?.setItem(key,value)},
  removeItem(key:string){browserStorage()?.removeItem(key)},
};

const refreshCoordinator=createRefreshCoordinator({
  storage:storageAdapter,
  fetchImpl:(input:RequestInfo|URL,init?:RequestInit)=>fetch(input,init),
  refreshUrl:`${apiRoot}/api/token/refresh/`,
});

async function responseError(response:Response,fallback:string){
  const raw=await response.text().catch(()=>"");
  return new Error(raw?userMessage(raw,response.status):fallback);
}

export function getAccessToken(){return readSession(storageAdapter).access as string|null}
export function getRefreshToken(){return readSession(storageAdapter).refresh as string|null}
export function hasStoredSession(){const x=readSession(storageAdapter);return Boolean(x.access||x.refresh)}
export function setSession(pair:TokenPair){writeSession(storageAdapter,pair)}
export function setAccessToken(access:string){storageAdapter.setItem(ACCESS_TOKEN_KEY,access)}
export function clearSession(){clearSessionStorage(storageAdapter)}

export async function loginWithPassword(username:string,password:string){
  let response:Response;
  try{
    response=await fetch(`${apiRoot}/api/token/`,{
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({username,password}),
      cache:"no-store",
    });
  }catch{throw new Error(t("error.network"))}
  if(!response.ok)throw await responseError(response,"نام کاربری یا گذرواژه نادرست است.");
  const pair=await response.json() as TokenPair;
  if(!pair.access||!pair.refresh)throw new Error("پاسخ ورود از سرور کامل نیست.");
  setSession(pair);
  return pair;
}

export async function requestLoginOtp(mobile:string):Promise<OtpRequestResponse>{
  let response:Response;
  try{
    response=await fetch(`${apiBase}/auth/login/otp/request/`,{
      method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({mobile}),cache:"no-store",
    });
  }catch{throw new Error(t("error.network"))}
  if(!response.ok)throw await responseError(response,t("error.generic"));
  return await response.json();
}

export async function loginWithOtp(challenge_id:string,code:string){
  let response:Response;
  try{
    response=await fetch(`${apiBase}/auth/login/otp/verify/`,{
      method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({challenge_id,code}),cache:"no-store",
    });
  }catch{throw new Error(t("error.network"))}
  if(!response.ok)throw await responseError(response,"کد ورود معتبر نیست.");
  const pair=await response.json() as TokenPair;
  if(!pair.access||!pair.refresh)throw new Error("پاسخ ورود از سرور کامل نیست.");
  setSession(pair);
  return pair;
}

export async function refreshSession(){return await refreshCoordinator()}

export function logout(redirect=true){
  clearSession();
  if(redirect&&typeof window!=="undefined"&&!location.pathname.startsWith("/login")){
    location.replace("/login");
  }
}

export {ACCESS_TOKEN_KEY,REFRESH_TOKEN_KEY};

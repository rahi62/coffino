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


async function publicPost<T>(path:string,payload:Record<string,unknown>):Promise<T>{
  let response:Response;
  try{
    response=await fetch(`${apiBase}${path}`,{
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify(payload),
      cache:"no-store",
    });
  }catch{throw new Error(t("error.network"))}
  if(!response.ok)throw await responseError(response,t("error.generic"));
  return await response.json() as T;
}

export type OtpVerificationResponse={detail:string;verification_grant:string};
export type SaasRegistrationInput={
  business_name:string;
  business_type:string;
  branch_name:string;
  branch_phone?:string;
  copy_owner_mobile_to_branch?:boolean;
  username:string;
  email?:string;
  password:string;
  password_confirmation:string;
  verification_grant:string;
};
export type SaasRegistrationResult={
  user:{id:number;username:string;email:string};
  business:{id:number;name:string};
  branch:{id:number;name:string};
  next:string;
};

export function requestRegistrationOtp(mobile:string){
  return publicPost<OtpRequestResponse>("/auth/register/otp/request/",{mobile});
}
export function verifyRegistrationOtp(challenge_id:string,code:string){
  return publicPost<OtpVerificationResponse>("/auth/register/otp/verify/",{challenge_id,code});
}
export function registerSaasOwner(input:SaasRegistrationInput){
  return publicPost<SaasRegistrationResult>("/auth/register/",input as unknown as Record<string,unknown>);
}
export function requestPasswordRecovery(identifier:string){
  return publicPost<OtpRequestResponse>("/auth/password/forgot/",{identifier});
}
export function verifyPasswordRecoveryOtp(challenge_id:string,code:string){
  return publicPost<OtpVerificationResponse>("/auth/password/otp/verify/",{challenge_id,code});
}
export function resetPassword(verification_grant:string,password:string,password_confirmation:string){
  return publicPost<{ok:boolean;detail:string}>("/auth/password/reset/",{
    verification_grant,password,password_confirmation,
  });
}

export async function refreshSession(){return await refreshCoordinator()}

export function logout(redirect=true){
  clearSession();
  if(redirect&&typeof window!=="undefined"&&!location.pathname.startsWith("/login")){
    location.replace("/login");
  }
}

export {ACCESS_TOKEN_KEY,REFRESH_TOKEN_KEY};

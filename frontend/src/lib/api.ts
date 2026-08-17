import { t, userMessage } from "@/lib/i18n";

const base=process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";
const tokenKey="cafino_access";
export function getToken(){if(typeof window==="undefined")return null;return localStorage.getItem(tokenKey)}
export function setToken(t:string){localStorage.setItem(tokenKey,t)}
export function clearToken(){localStorage.removeItem(tokenKey)}
export async function login(username:string,password:string){
 let r:Response;try{r=await fetch((process.env.NEXT_PUBLIC_API_ROOT||"http://127.0.0.1:8000")+"/api/token/",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({username,password})});}catch{throw new Error(t("error.network"));}if(!r.ok)throw new Error("نام کاربری یا رمز عبور نادرست است.");const d=await r.json();setToken(d.access);return d;
}

function headerValue(headers:HeadersInit|undefined,name:string){
 if(!headers)return "";if(headers instanceof Headers)return headers.get(name)||"";
 if(Array.isArray(headers)){const row=headers.find(([k])=>k.toLowerCase()===name.toLowerCase());return row?.[1]||""}
 const record=headers as Record<string,string>;const key=Object.keys(record).find(k=>k.toLowerCase()===name.toLowerCase());return key?String(record[key]||""):"";
}
async function authorizeLocalPos(path:string,init?:RequestInit):Promise<RequestInit|undefined>{
 if(path!=="/checkout/"||typeof window==="undefined"||!init?.body||typeof init.body!=="string")return init;
 const bridge=(window as any).cafino;if(!bridge?.sendPosAmount||!bridge?.deviceAdapters)return init;
 let registry:any;try{registry=await bridge.deviceAdapters()}catch{return init}
 const selected=String(registry?.groups?.POS?.selected||"MANUAL").toUpperCase();if(selected==="MANUAL")return init;
 let payload:any;try{payload=JSON.parse(init.body)}catch{return init}
 if(payload?.defer_payment||!Array.isArray(payload?.payments))return init;
 const pendingPos=payload.payments.filter((payment:any)=>payment?.method==="POS"&&!payment?.reference_number);
 if(pendingPos.length>1)throw new Error("برای جلوگیری از برداشت ناقص در پرداخت چندنفره، اتصال مستقیم کارت‌خوان فعلاً فقط یک سهم POS را در هر ثبت سفارش خودکار می‌کند. سایر سهم‌ها را دستی تسویه کنید.");
 const key=headerValue(init.headers,"Idempotency-Key")||globalThis.crypto?.randomUUID?.()||String(Date.now());
 const payments=[];
 for(let i=0;i<payload.payments.length;i++){
   const payment={...payload.payments[i]};
   if(payment.method==="POS"&&!payment.reference_number){
     const amount=Number(payment.amount||0);if(!Number.isSafeInteger(amount)||amount<=0)throw new Error("مبلغ کارت‌خوان معتبر نیست.");
     const terminalReference=`${key}:pos:${i}`.replace(/[^A-Za-z0-9_.:-]/g,"").slice(0,80);
     const result=await bridge.sendPosAmount({amount,reference:terminalReference,payerLabel:payment.payer_label||""});
     if(!result?.ok||result?.approved===false){
       throw new Error(result?.message||"تراکنش کارت‌خوان تأیید نشد؛ سفارش ثبت نشده است.");
     }
     payment.reference_number=String(result.referenceNumber||result.traceNumber||terminalReference).slice(0,120);
   }
   payments.push(payment);
 }
 return{...init,body:JSON.stringify({...payload,payments})};
}

export async function api<T>(path:string, init?:RequestInit):Promise<T>{
 const prepared=await authorizeLocalPos(path,init);
 const token=getToken();let r:Response;try{r=await fetch(`${base}${path}`,{...prepared,headers:{"Content-Type":"application/json",...(token?{Authorization:`Bearer ${token}`} :{}),...(prepared?.headers||{})},cache:"no-store"});}catch(error){if(error instanceof Error&&error.message&&!error.message.includes("fetch"))throw error;throw new Error(t("error.network"));}
 if(r.status===401){if(typeof window!=="undefined" && !location.pathname.startsWith("/login"))location.href="/login";throw new Error(t("error.unauthorized"))}
 if(!r.ok)throw new Error(userMessage(await r.text(),r.status));
 if(r.status===204)return undefined as T;
 const body=await r.text();
 if(!body.trim())return undefined as T;
 try{return JSON.parse(body) as T}catch{throw new Error("پاسخ دریافتی از سرور قابل پردازش نیست. لطفاً دوباره تلاش کنید.")}
}
export {base};

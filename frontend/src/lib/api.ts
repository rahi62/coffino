const base=process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";
const tokenKey="cafino_access";
export function getToken(){if(typeof window==="undefined")return null;return localStorage.getItem(tokenKey)}
export function setToken(t:string){localStorage.setItem(tokenKey,t)}
export function clearToken(){localStorage.removeItem(tokenKey)}
export async function login(username:string,password:string){
 const r=await fetch((process.env.NEXT_PUBLIC_API_ROOT||"http://127.0.0.1:8000")+"/api/token/",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({username,password})});if(!r.ok)throw new Error("نام کاربری یا رمز عبور اشتباه است");const d=await r.json();setToken(d.access);return d;
}
export async function api<T>(path:string, init?:RequestInit):Promise<T>{
 const token=getToken();const r=await fetch(`${base}${path}`,{...init,headers:{"Content-Type":"application/json",...(token?{Authorization:`Bearer ${token}`} :{}),...(init?.headers||{})},cache:"no-store"});
 if(r.status===401){if(typeof window!=="undefined" && !location.pathname.startsWith("/login"))location.href="/login";throw new Error("Unauthorized")}
 if(!r.ok)throw new Error(await r.text());return r.json();
}
export {base};

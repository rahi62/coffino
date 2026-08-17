"use client";
import Link from "next/link";
import {usePathname} from "next/navigation";
import {Building2,Store,Armchair,ReceiptText,Boxes,Globe2,MessageSquare,UsersRound,Settings2,ChevronLeft} from "lucide-react";
import {SettingsProvider,useSettings} from "./settings-context";

const nav=[
 ["/settings","نمای کلی",Settings2,null],
 ["/settings/business","کسب‌وکار و ماژول‌ها",Building2,"business.manage"],
 ["/settings/branches","شعب و صندوق‌ها",Store,"branches.manage"],
 ["/settings/dining","سالن و تعریف میز",Armchair,"settings.manage"],
 ["/settings/sales","فروش و مالی",ReceiptText,"settings.manage"],
 ["/settings/catalog","منو و موجودی",Boxes,"inventory.manage"],
 ["/settings/online","سفارش آنلاین و ارسال",Globe2,"online_ordering.manage"],
 ["/settings/notifications","اطلاع‌رسانی",MessageSquare,"notifications.manage"],
 ["/settings/team","کاربران و دسترسی‌ها",UsersRound,"permissions.manage"],
] as const;

function Inner({children}:{children:React.ReactNode}){
 const path=usePathname();const {data,loading,error,selectedBranchId,setSelectedBranchId,can}=useSettings();
 if(loading)return <div className="card p-6">در حال بارگذاری تنظیمات…</div>;
 if(error)return <div className="card p-6 border-red-200"><b>دسترسی به تنظیمات ممکن نیست.</b><div className="text-sm text-red-700 mt-2">{error}</div></div>;
 if(!data)return null;
 const items=nav.filter(x=>!x[3]||can(x[3]));
 return <div className="space-y-5">
   <div className="card p-4 flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
    <div><div className="text-xs text-[#8d8178]">تنظیمات کافینو</div><h1 className="text-2xl font-black">{data.business.name}</h1></div>
    <div className="flex flex-wrap items-center gap-2"><span className="badge">{data.role}</span>{data.branches.length>0&&<select className="btn min-w-48" value={selectedBranchId||""} onChange={e=>setSelectedBranchId(Number(e.target.value))}>{data.branches.map(b=><option key={b.id} value={b.id}>{b.name}</option>)}</select>}<Link href="/" className="btn flex items-center gap-1"><ChevronLeft size={16}/> داشبورد</Link></div>
   </div>
   <div className="grid xl:grid-cols-[235px_1fr] gap-5 items-start">
    <aside className="card p-2 xl:sticky xl:top-5">{items.map(([href,label,Icon])=>{const active=href==="/settings"?path===href:path===href||path.startsWith(`${href}/`);return <Link key={href} href={href} className={`flex items-center gap-2 rounded-xl px-3 py-3 text-sm mb-1 ${active?"bg-[#211711] text-white font-bold":"hover:bg-[#eee6dc]"}`}><Icon size={17}/>{label}</Link>})}</aside>
    <section className="min-w-0">{children}</section>
   </div>
 </div>
}
export default function SettingsShell({children}:{children:React.ReactNode}){return <SettingsProvider><Inner>{children}</Inner></SettingsProvider>}

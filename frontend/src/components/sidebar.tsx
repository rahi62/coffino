"use client";
import Link from "next/link";
import {usePathname} from "next/navigation";
import {useEffect,useState} from "react";
import {LayoutDashboard,ShoppingCart,ClipboardList,UtensilsCrossed,Package,Armchair,ShoppingBag,LogOut,HardDrive,WalletCards,Truck,Boxes,FlaskConical,BarChart3,ReceiptText,UsersRound,ShieldCheck,FileClock,CalendarCheck2,LineChart,Settings2,BadgePercent,UserRoundCheck,Trash2,Building2,ClipboardCheck,ArrowRightLeft,Factory,CalendarDays,Gift,Layers3,PackageSearch,Bike,ArrowLeftRight,ScanLine,ChevronDown,Menu,X} from "lucide-react";
import {api,clearToken} from "@/lib/api";
import {localizeLegacyText,t} from "@/lib/i18n";
import {reduceMobileNavigation} from "./mobile-navigation-state.mjs";
import {isPublicRoute} from "@/lib/public-routes.mjs";
import {mobileActions,permittedActions,routeIsActive} from "@/lib/dashboard-actions.mjs";
const links:any[]=[
["/","داشبورد",LayoutDashboard,null],["/pos","فروش جدید",ShoppingCart,"orders.create"],["/orders","سفارش‌ها",ClipboardList,"orders.view"],["/split-bill","تقسیم صورتحساب",Layers3,"payments.split"],["/order-transfer","انتقال سفارش/میز",ArrowLeftRight,"orders.transfer"],["/tables","سالن و میزها",Armchair,"tables.use"],["/reservations","رزرو میز",CalendarDays,"reservations.manage"],["/takeaway","بیرون‌بر",ShoppingBag,"orders.view"],["/kitchen","آشپزخانه",UtensilsCrossed,"kitchen.view"],
["/cashier","صندوق و شیفت",WalletCards,"cashier.use"],["/purchasing","خرید",Truck,"purchasing.view"],["/suppliers","تأمین‌کنندگان",UsersRound,"suppliers.view"],["/expenses","هزینه‌ها",ReceiptText,"expenses.manage"],["/products","محصولات",Boxes,"inventory.manage"],["/recipes","رسپی ساز",FlaskConical,"inventory.manage"],["/inventory","انبار",Package,"inventory.view"],["/inventory-lots","Lot / FEFO",PackageSearch,"inventory.view"],["/inventory-control","شمارش فیزیکی",ClipboardCheck,"inventory.count"],["/lot-count","شمارش Lot",ScanLine,"inventory.lot_count"],["/stock-transfers","انتقال شعب",ArrowRightLeft,"inventory.transfer"],["/production","تولید Batch",Factory,"production.manage"],
["/waste","ضایعات و بهای مواد مصرفی",Trash2,"food_cost.view"],["/reports","سود و نقطه سربه‌سر",BarChart3,"reports.view"],["/kpi","KPI مدیریتی",BarChart3,"reports.view"],["/sales-analytics","تحلیل فروش",LineChart,"reports.view"],["/branches-dashboard","چندشعبه‌ای",Building2,"branches.dashboard"],
["/customers-loyalty","مشتری و Loyalty",Gift,"loyalty.manage"],["/gift-cards","کارت هدیه",Gift,"giftcards.manage"],["/delivery","ارسال و پیک",Bike,"delivery.manage"],["/workforce","کارکنان و حضور",UserRoundCheck,"workforce.clock"],["/discounts","قوانین تخفیف",BadgePercent,"discount.rules.manage"],["/approvals","تأییدهای مدیر",ShieldCheck,"approvals.decide"],["/daily-close","بستن روز مالی",CalendarCheck2,"daily_close.execute"],["/settings","تنظیمات کسب‌وکار",Settings2,"settings.manage"],["/operations","Production Operations",HardDrive,"operations.view"],["/audit","Audit Log",FileClock,"audit.view"],["/local-tools","ابزار Local",HardDrive,null]
];
const sections=[
 {id:"main",title:"اصلی",hrefs:["/"]},
 {id:"sales",title:"فروش و سفارش",hrefs:["/pos","/orders","/split-bill","/order-transfer","/takeaway","/cashier"]},
 {id:"service",title:"سالن و آماده‌سازی",hrefs:["/tables","/reservations","/kitchen"]},
 {id:"inventory",title:"خرید و انبار",hrefs:["/purchasing","/suppliers","/products","/recipes","/inventory","/inventory-lots","/inventory-control","/lot-count","/stock-transfers","/production","/waste"]},
 {id:"customers",title:"مشتری و کانال فروش",hrefs:["/customers-loyalty","/gift-cards","/delivery","/discounts"]},
 {id:"reports",title:"مالی و گزارش‌ها",hrefs:["/expenses","/reports","/kpi","/sales-analytics","/branches-dashboard","/daily-close"]},
 {id:"management",title:"مدیریت سامانه",hrefs:["/settings","/operations","/workforce","/approvals","/audit","/local-tools"]},
];
export default function Sidebar(){
 const [perms,setPerms]=useState<Record<string,boolean>|null>(null);
 const [mobileOpen,setMobileOpen]=useState(false);
 const pathname=usePathname();
 const activeSection=sections.find(section=>section.hrefs.some(href=>href==="/"?pathname==="/":pathname===href||pathname.startsWith(`${href}/`)))?.id||"main";
 const [openSections,setOpenSections]=useState<Record<string,boolean>>(()=>({main:true,[activeSection]:true}));
 useEffect(()=>{const reload=()=>{if(!isPublicRoute(pathname))api<any>("/permissions/me/").then(x=>setPerms(x.permissions)).catch(()=>setPerms({}))};reload();window.addEventListener("cafino-permissions-changed",reload);return()=>window.removeEventListener("cafino-permissions-changed",reload)},[pathname]);
 useEffect(()=>{setOpenSections(current=>({...current,[activeSection]:true}));setMobileOpen(current=>reduceMobileNavigation(current,"navigate"))},[activeSection,pathname]);
 useEffect(()=>{
  if(!mobileOpen)return;
  const previous=document.body.style.overflow;
  document.body.style.overflow="hidden";
  return()=>{document.body.style.overflow=previous};
 },[mobileOpen]);
 useEffect(()=>{const close=(event:KeyboardEvent)=>{if(event.key==="Escape")setMobileOpen(false)};window.addEventListener("keydown",close);return()=>window.removeEventListener("keydown",close)},[]);
 if(isPublicRoute(pathname))return null;
 const visible=links.filter(x=>!x[3]||(perms!==null&&perms[x[3]]));
 const isActive=(href:string)=>href==="/"?pathname==="/":pathname===href||pathname.startsWith(`${href}/`);
 const renderNav=(prefixId:string,touch:boolean)=><nav className="sidebar-scroll min-h-0 flex-1 space-y-3 overflow-y-auto overscroll-contain pb-3" aria-label="منوی اصلی">{sections.map(section=>{const rows=visible.filter(([href])=>section.hrefs.includes(href));if(!rows.length)return null;const expanded=Boolean(openSections[section.id]);return <section key={section.id} aria-label={section.title}><button type="button" className={`flex w-full items-center justify-between rounded-lg px-2 ${touch?"min-h-11 py-2":"py-2"} text-right text-xs font-bold tracking-wide text-white/55 transition-colors hover:bg-white/5 hover:text-white`} onClick={()=>setOpenSections(current=>({...current,[section.id]:!current[section.id]}))} aria-expanded={expanded} aria-controls={`${prefixId}-${section.id}`}><span>{section.title}</span><ChevronDown size={16} className={`transition-transform ${expanded?"rotate-180":""}`} aria-hidden="true"/></button>{expanded&&<div id={`${prefixId}-${section.id}`} className="mt-1 space-y-1">{rows.map(([href,label,Icon])=>{const active=isActive(href);return <Link key={href} href={href} aria-current={active?"page":undefined} className={`flex ${touch?"min-h-12":"min-h-11"} items-center gap-3 rounded-xl border-r-4 px-3 py-2.5 transition-colors ${active?"border-[#e5ad62] bg-[#b9792d] font-bold text-white shadow-[0_6px_18px_rgba(185,121,45,.28)]":"border-transparent text-white/80 hover:bg-white/10 hover:text-white"}`}><Icon size={18} strokeWidth={active?2.5:2} className="flex-none"/><span className="min-w-0 break-words">{localizeLegacyText(label)}</span></Link>})}</div>}</section>})}</nav>;
 const logout=()=>{clearToken();location.href="/login"};
 return <>
  <header className="fixed inset-x-0 top-0 z-40 flex h-14 items-center justify-between border-b border-white/10 bg-[#211711] px-3 text-white shadow-lg md:hidden">
   <div className="min-w-0"><div className="text-lg font-black leading-none">کافینو</div><div className="mt-1 truncate text-[11px] text-white/55">مدیریت کافه و رستوران</div></div>
   <button data-testid="mobile-nav-trigger" type="button" className="grid h-11 w-11 place-items-center rounded-xl bg-white/10 text-white transition hover:bg-white/15" onClick={()=>setMobileOpen(current=>reduceMobileNavigation(current,"open"))} aria-label="باز کردن منوی اصلی" aria-expanded={mobileOpen} aria-controls="cafino-primary-navigation"><Menu size={22} aria-hidden="true"/></button>
  </header>
  <nav aria-label="ناوبری سریع موبایل" className="fixed inset-x-0 bottom-0 z-30 flex min-h-16 items-stretch justify-around border-t border-[#eadfd3] bg-[#fffdf9] px-1 pt-1 shadow-[0_-5px_18px_rgba(33,23,17,.08)] md:hidden" style={{paddingBottom:"env(safe-area-inset-bottom, 0px)"}}>
    {permittedActions(mobileActions,perms).map(item=>{
      const active=routeIsActive(pathname,item.href);
      const Icon=item.href==="/"?LayoutDashboard:item.href==="/pos"?ShoppingCart:item.href==="/orders"?ClipboardList:Armchair;
      return <Link key={item.href} href={item.href} aria-current={active?"page":undefined} className={`flex min-h-14 min-w-14 flex-1 flex-col items-center justify-center gap-0.5 rounded-xl px-1 text-[11px] font-bold ${active?"bg-[#f7e9d5] text-[#89571e]":"text-[#685749]"}`}><Icon aria-hidden="true" size={21}/>{item.label}</Link>;
    })}
    {perms===null&&<span role="status" className="flex min-h-14 items-center text-xs text-[#8d8178]">در حال بررسی دسترسی‌ها…</span>}
  </nav>

  <aside aria-label="منوی میان‌بر" className="sidebar-scroll sticky top-0 hidden h-screen w-[76px] shrink-0 flex-col items-center gap-1 overflow-y-auto bg-[#211711] py-3 text-white md:flex xl:hidden">
   <button type="button" aria-label="باز کردن منوی کامل" aria-expanded={mobileOpen} className="mb-2 grid size-12 shrink-0 place-items-center rounded-xl bg-white/10 hover:bg-white/20" onClick={()=>setMobileOpen(current=>reduceMobileNavigation(current,"open"))}><Menu size={22} aria-hidden="true"/></button>
   {visible.map(([href,label,Icon])=>{const active=isActive(href);return <Link key={href} href={href} title={localizeLegacyText(label)} aria-label={localizeLegacyText(label)} aria-current={active?"page":undefined} className={`grid size-12 shrink-0 place-items-center rounded-xl transition-colors ${active?"bg-[#b9792d] text-white shadow-[0_6px_18px_rgba(185,121,45,.28)]":"text-white/75 hover:bg-white/10 hover:text-white"}`}><Icon size={20} strokeWidth={active?2.5:2} aria-hidden="true"/></Link>})}
   <button type="button" aria-label={t("nav.logout","خروج")} title={t("nav.logout","خروج")} className="mt-3 grid size-12 shrink-0 place-items-center rounded-xl text-white/70 hover:bg-white/10 hover:text-white" onClick={logout}><LogOut size={20} aria-hidden="true"/></button>
  </aside>

  <aside className="sidebar-scroll sticky top-0 hidden h-screen w-64 shrink-0 flex-col bg-[#211711] p-4 text-white xl:flex">
   <div className="mb-6 text-2xl font-black">کافینو</div>
   {renderNav("sidebar-desktop",false)}
   <button className="mt-3 flex min-h-11 flex-none items-center gap-2 border-t border-white/10 pt-4 text-white/70 transition-colors hover:text-white" onClick={logout}><LogOut size={18}/>{t("nav.logout","خروج")}</button>
  </aside>

  {mobileOpen&&<div className="fixed inset-0 z-50 xl:hidden">
   <button type="button" className="absolute inset-0 h-full w-full cursor-default bg-black/45 backdrop-blur-[1px]" onClick={()=>setMobileOpen(false)} aria-label="بستن منوی اصلی"/>
   <aside id="cafino-primary-navigation" role="dialog" aria-modal="true" aria-label="منوی اصلی" className="absolute inset-y-0 right-0 flex h-[100dvh] w-[min(20rem,88vw)] flex-col bg-[#211711] p-4 text-white shadow-2xl">
    <div className="mb-4 flex items-center justify-between gap-3"><div className="min-w-0"><div className="text-2xl font-black">کافینو</div><div className="mt-1 text-xs text-white/45">منوی اصلی</div></div><button type="button" className="grid h-11 w-11 flex-none place-items-center rounded-xl bg-white/10 transition hover:bg-white/15" onClick={()=>setMobileOpen(false)} aria-label="بستن منوی اصلی"><X size={20} aria-hidden="true"/></button></div>
    {renderNav("sidebar-drawer",true)}
    <button className="mt-3 flex min-h-12 flex-none items-center gap-2 border-t border-white/10 pt-4 text-white/70 transition-colors hover:text-white" onClick={logout}><LogOut size={18}/>{t("nav.logout","خروج")}</button>
   </aside>
  </div>}
 </>;
}

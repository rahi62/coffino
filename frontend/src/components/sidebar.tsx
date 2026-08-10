"use client";
import Link from "next/link";
import {usePathname} from "next/navigation";
import {useEffect,useState} from "react";
import {LayoutDashboard,ShoppingCart,ClipboardList,UtensilsCrossed,Package,Armchair,ShoppingBag,LogOut,HardDrive,WalletCards,Truck,Boxes,FlaskConical,BarChart3,ReceiptText,UsersRound,ShieldCheck,FileClock,CalendarCheck2,LineChart,Settings2,BadgePercent,UserRoundCheck,Trash2,Building2,ClipboardCheck,ArrowRightLeft,Factory,Percent,Printer,CalendarDays,Gift,MessageSquare,Globe2,Layers3,PackageSearch,Bike,CreditCard,ArrowLeftRight,ScanLine,ChevronDown,Menu,X} from "lucide-react";
import {api,clearToken} from "@/lib/api";
import {localizeLegacyText,t} from "@/lib/i18n";
const links:any[]=[
["/","داشبورد",LayoutDashboard,null],["/pos","فروش جدید",ShoppingCart,"orders.create"],["/orders","سفارش‌ها",ClipboardList,"orders.view"],["/split-bill","تقسیم صورتحساب",Layers3,"payments.split"],["/order-transfer","انتقال سفارش/میز",ArrowLeftRight,"orders.transfer"],["/tables","سالن و میزها",Armchair,"tables.use"],["/reservations","رزرو میز",CalendarDays,"reservations.manage"],["/takeaway","بیرون‌بر",ShoppingBag,"orders.view"],["/kitchen","آشپزخانه",UtensilsCrossed,"kitchen.view"],
["/cashier","صندوق و شیفت",WalletCards,"cashier.use"],["/purchasing","خرید",Truck,"purchasing.view"],["/suppliers","تأمین‌کنندگان",UsersRound,"suppliers.view"],["/expenses","هزینه‌ها",ReceiptText,"expenses.manage"],["/products","محصولات",Boxes,"inventory.manage"],["/recipes","رسپی ساز",FlaskConical,"inventory.manage"],["/inventory","انبار",Package,"inventory.view"],["/inventory-lots","بچ و اولویت انقضا",PackageSearch,"inventory.view"],["/inventory-control","شمارش فیزیکی",ClipboardCheck,"inventory.count"],["/lot-count","شمارش بچ",ScanLine,"inventory.lot_count"],["/stock-transfers","انتقال شعب",ArrowRightLeft,"inventory.transfer"],["/production","تولید دسته‌ای",Factory,"production.manage"],
["/waste","ضایعات و بهای مواد مصرفی",Trash2,"food_cost.view"],["/reports","سود و نقطه سربه‌سر",BarChart3,"reports.view"],["/kpi","شاخص‌های مدیریتی",BarChart3,"reports.view"],["/sales-analytics","تحلیل فروش",LineChart,"reports.view"],["/branches-dashboard","چندشعبه‌ای",Building2,"branches.dashboard"],["/fiscal","مالیات و حق سرویس",Percent,"fiscal.manage"],["/printing","پرینترها",Printer,"printing.manage"],
["/customers-loyalty","مشتری و وفاداری",Gift,"loyalty.manage"],["/gift-cards","کارت هدیه",Gift,"giftcards.manage"],["/delivery","ارسال و پیک",Bike,"delivery.manage"],["/payment-gateway","درگاه پرداخت",CreditCard,"payment_gateway.manage"],["/notifications","اعلان و پیامک",MessageSquare,"notifications.manage"],["/online-ordering","سفارش آنلاین و بارکد دوبعدی",Globe2,"online_ordering.manage"],["/workforce","کارکنان و حضور",UserRoundCheck,"workforce.clock"],["/discounts","قوانین تخفیف",BadgePercent,"discount.rules.manage"],["/approvals","تأییدهای مدیر",ShieldCheck,"approvals.decide"],["/daily-close","بستن روز مالی",CalendarCheck2,"daily_close.execute"],["/settings","تنظیمات کسب‌وکار",Settings2,"settings.manage"],["/permissions","دسترسی‌ها",Settings2,"permissions.manage"],["/audit","گزارش ممیزی",FileClock,"audit.view"],["/local-tools","ابزار محلی",HardDrive,null]
];
const sections=[
 {id:"main",title:"اصلی",hrefs:["/"]},
 {id:"sales",title:"فروش و سفارش",hrefs:["/pos","/orders","/split-bill","/order-transfer","/takeaway","/cashier"]},
 {id:"service",title:"سالن و آماده‌سازی",hrefs:["/tables","/reservations","/kitchen"]},
 {id:"inventory",title:"خرید و انبار",hrefs:["/purchasing","/suppliers","/products","/recipes","/inventory","/inventory-lots","/inventory-control","/lot-count","/stock-transfers","/production","/waste"]},
 {id:"customers",title:"مشتری و کانال فروش",hrefs:["/customers-loyalty","/gift-cards","/delivery","/payment-gateway","/notifications","/online-ordering","/discounts"]},
 {id:"reports",title:"مالی و گزارش‌ها",hrefs:["/expenses","/reports","/kpi","/sales-analytics","/branches-dashboard","/fiscal","/daily-close"]},
 {id:"management",title:"مدیریت سامانه",hrefs:["/printing","/settings","/workforce","/approvals","/permissions","/audit","/local-tools"]},
];
export default function Sidebar(){
 const [perms,setPerms]=useState<Record<string,boolean>|null>(null);
 const pathname=usePathname();
 const [mobileOpen,setMobileOpen]=useState(false);
 const activeSection=sections.find(section=>section.hrefs.some(href=>href==="/"?pathname==="/":pathname===href||pathname.startsWith(`${href}/`)))?.id||"main";
 const [openSections,setOpenSections]=useState<Record<string,boolean>>(()=>({main:true,[activeSection]:true}));
 useEffect(()=>{if(location.pathname!=="/login"&&!location.pathname.startsWith("/menu/"))api<any>("/permissions/me/").then(x=>setPerms(x.permissions)).catch(()=>setPerms({}))},[]);
 useEffect(()=>{setOpenSections(current=>({...current,[activeSection]:true}))},[activeSection]);
 if(typeof window!=="undefined"&&(location.pathname==="/login"||location.pathname.startsWith("/menu/")))return null;
 const visible=links.filter(x=>!x[3]||(perms!==null&&perms[x[3]]));
 return <>
  <button type="button" className="fixed right-3 top-3 z-40 grid h-11 w-11 place-items-center rounded-xl bg-[#211711] text-white shadow-lg lg:hidden" onClick={()=>setMobileOpen(true)} aria-label="باز کردن منو" aria-expanded={mobileOpen} aria-controls="mobile-sidebar"><Menu size={22}/></button>
  {mobileOpen&&<button type="button" className="fixed inset-0 z-40 bg-black/35 lg:hidden" onClick={()=>setMobileOpen(false)} aria-label="بستن منو"/>}
  <aside id="mobile-sidebar" className={`fixed inset-y-0 right-0 z-50 flex max-h-screen min-h-screen w-72 max-w-[88vw] flex-col overflow-y-auto bg-[#211711] p-4 text-white shadow-2xl transition-transform duration-200 lg:sticky lg:inset-auto lg:top-0 lg:z-auto lg:w-64 lg:max-w-none lg:translate-x-0 lg:shadow-none ${mobileOpen?"translate-x-0":"translate-x-full"}`}>
   <div className="mb-6 flex items-center justify-between text-2xl font-black"><span>کافینو</span><button type="button" className="rounded-lg p-2 text-white/80 hover:bg-white/10 lg:hidden" onClick={()=>setMobileOpen(false)} aria-label="بستن منو"><X size={22}/></button></div>
   <nav className="space-y-3">{sections.map(section=>{const rows=visible.filter(([href])=>section.hrefs.includes(href));if(!rows.length)return null;const expanded=Boolean(openSections[section.id]);return <section key={section.id} aria-label={section.title}><button type="button" className="flex w-full items-center justify-between rounded-lg px-2 py-1.5 text-right text-xs font-bold tracking-wide text-white/55 transition-colors hover:bg-white/5 hover:text-white" onClick={()=>setOpenSections(current=>({...current,[section.id]:!current[section.id]}))} aria-expanded={expanded} aria-controls={`sidebar-${section.id}`}><span>{localizeLegacyText(section.title)}</span><ChevronDown size={16} className={`transition-transform ${expanded?"rotate-180":""}`} aria-hidden="true"/></button>{expanded&&<div id={`sidebar-${section.id}`} className="mt-1 space-y-1">{rows.map(([href,label,Icon])=>{const active=href==="/"?pathname==="/":pathname===href||pathname.startsWith(`${href}/`);return <Link key={href} href={href} onClick={()=>setMobileOpen(false)} aria-current={active?"page":undefined} className={`flex items-center gap-3 rounded-xl border-r-4 px-3 py-2.5 transition-colors ${active?"border-[#e5ad62] bg-[#b9792d] font-bold text-white shadow-[0_6px_18px_rgba(185,121,45,.28)]":"border-transparent text-white/80 hover:bg-white/10 hover:text-white"}`}><Icon size={18} strokeWidth={active?2.5:2}/>{localizeLegacyText(label)}</Link>})}</div>}</section>})}</nav>
   <button className="mt-8 flex items-center gap-2 border-t border-white/10 pt-5 text-white/70 transition-colors hover:text-white" onClick={()=>{clearToken();location.href="/login"}}><LogOut size={18}/>{t("nav.logout","خروج")}</button>
  </aside>
 </>
}

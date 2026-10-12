"use client";
import Link from "next/link";
import {AlertTriangle,Armchair,Boxes,Building2,CheckCircle2,CircleAlert,Globe2,MessageSquare,ReceiptText,Settings2,ShieldCheck,Store,UsersRound} from "lucide-react";
import {BranchReadiness,SetupCheck,useSettings} from "@/components/settings/settings-context";

const cards=[
 ["/settings/onboarding","راه‌اندازی هوشمند","انتخاب الگوی کسب‌وکار، راه‌اندازی اولیه و بررسی سلامت اتصال‌ها",Settings2,"business.manage"],
 ["/settings/go-live","آماده‌سازی انتشار و تحویل","بررسی آمادگی انتشار، شیوه استقرار، پشتیبان‌گیری و بازیابی و پیش‌نیازهای اجرا",ShieldCheck,"settings.manage"],
 ["/settings/business","پروفایل کسب‌وکار","نام، نوع مجموعه، مدل استقرار و ماژول‌های فعال",Building2,"business.manage"],
 ["/settings/branches","شعب و صندوق‌ها","اطلاعات شعب، شماره تماس، صندوق‌های فروش",Store,"branches.manage"],
 ["/settings/dining","سالن و میزها","تعریف سالن، شماره میز و ظرفیت",Armchair,"settings.manage"],
 ["/settings/sales","فروش و مالی","مالیات، حق سرویس، صندوق و چاپ",ReceiptText,"settings.manage"],
 ["/settings/catalog","منو و موجودی","محصول، دسته، رسپی و انبار",Boxes,"inventory.manage"],
 ["/settings/online","سفارش آنلاین","کد اسکن، تحویل، ارسال، محدوده و درگاه",Globe2,"online_ordering.manage"],
 ["/settings/notifications","اطلاع‌رسانی","پیامک، اعلان دستگاه و صف اطلاع‌رسانی",MessageSquare,"notifications.manage"],
 ["/settings/team","تیم و دسترسی","ساخت کاربر، تعیین نقش، شعبه و سطح دسترسی",UsersRound,"permissions.manage"],
] as const;

export default function SettingsHome(){
 const {data,readiness,selectedBranchId,can}=useSettings();
 if(!data||!readiness)return null;
 const enabled=data.modules.filter(x=>x.enabled).length;
 const branch=readiness.branches.find(x=>x.branch===selectedBranchId)||readiness.branches[0]||null;
 const pending=[...readiness.business.checks,...(branch?.checks||[])].filter(x=>x.status!=="done");
 const canOnboard=can("business.manage");
 return <div>
  <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-end md:justify-between"><div><h2 className="text-3xl font-black">مرکز تنظیمات</h2><p className="text-[#8d8178] mt-1">راه‌اندازی و تنظیمات روزمره کسب‌وکار از همین داشبورد انجام می‌شود؛ Django Admin فقط برای پشتیبانی پلتفرم باقی می‌ماند.</p></div><div className="flex flex-wrap gap-2">{canOnboard&&<Link href="/settings/onboarding" className="btn">راه‌اندازی هوشمند</Link>}<Link href="/settings/go-live" className="btn btn-primary">بررسی آمادگی انتشار</Link></div></div>

  <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-3 mb-5">
   <Metric label="آمادگی راه‌اندازی" value={`${readiness.overall.score}%`} detail={`${readiness.overall.completed} از ${readiness.overall.total} مورد ضروری`}/>
   <Metric label="موارد ضروری ناقص" value={String(readiness.overall.blocking)} detail={readiness.overall.blocking?"برای راه‌اندازی کامل باید رفع شوند":"تنظیمات ضروری کامل است"}/>
   <Metric label="شعب فعال" value={String(data.branches.filter(b=>b.is_active).length)} detail={branch?`شعبه انتخابی: ${branch.name}`:"هنوز شعبه فعالی ندارید"}/>
   <Metric label="مدل استقرار / ماژول" value={({LOCAL:"محلی",SAAS:"ابری",DEDICATED:"اختصاصی"} as Record<string,string>)[data.business.deployment_type]||"نامشخص"} detail={`${enabled} ماژول صریحاً فعال`}/>
  </div>

  <div className="card p-5 mb-5">
   <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between"><div><div className="flex items-center gap-2"><Settings2 size={20}/><h3 className="font-black text-lg">وضعیت آمادگی راه‌اندازی</h3></div><p className="text-sm text-[#8d8178] mt-1">بر اساس ماژول‌های فعال، Cafino تنظیمات لازم هر شعبه را به‌صورت خودکار بررسی می‌کند.</p></div><div className="text-left"><b className="text-3xl">{readiness.overall.score}%</b><div className="text-xs text-[#8d8178]">آمادگی کل مجموعه</div></div></div>
   <div className="h-3 rounded-full bg-[#eee6dc] overflow-hidden mt-4"><div className="h-full bg-emerald-600 transition-all" style={{width:`${readiness.overall.score}%`}}/></div>
   {readiness.overall.blocking>0?<div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-3 flex gap-2 items-start"><AlertTriangle className="text-amber-700 shrink-0" size={19}/><div className="flex-1"><b className="text-sm">{readiness.overall.blocking} تنظیم ضروری هنوز کامل نیست.</b><p className="text-xs text-amber-900/70 mt-1">فهرست زیر دقیقاً مشخص می‌کند از کدام صفحه باید هر مورد را تکمیل کنید.</p></div>{canOnboard&&<Link href="/settings/onboarding" className="btn shrink-0">راهنمای راه‌اندازی</Link>}</div>:<div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 p-3 flex gap-2 items-center"><CheckCircle2 className="text-emerald-700" size={19}/><div className="flex-1"><b className="text-sm">تنظیمات عملیاتی کامل است.</b><p className="text-xs text-emerald-900/70 mt-1">مرحله بعد: بررسی آمادگی انتشار، امنیت، پشتیبان‌گیری و محیط اجرا.</p></div><Link href="/settings/go-live" className="btn shrink-0">بررسی تحویل</Link></div>}
  </div>

  <div className="grid xl:grid-cols-[1.25fr_.75fr] gap-5 mb-6">
   <section className="card p-5"><div className="flex items-center justify-between gap-3"><div><h3 className="font-black text-lg">فهرست بررسی راه‌اندازی</h3><p className="text-xs text-[#8d8178] mt-1">کسب‌وکار و {branch?.name||"شعبه"}</p></div><span className="badge">{pending.length} نیازمند توجه</span></div><div className="mt-4 space-y-2">{readiness.business.checks.map(x=><CheckRow key={`business-${x.key}`} check={x}/>)}{branch?.checks.map(x=><CheckRow key={`branch-${x.key}`} check={x}/>)}</div></section>
   <section className="card p-5"><h3 className="font-black text-lg">آمادگی شعب</h3><p className="text-xs text-[#8d8178] mt-1">امتیاز فقط موارد ضروری مرتبط با ماژول‌های فعال را حساب می‌کند.</p><div className="mt-4 space-y-3">{readiness.branches.length?readiness.branches.map(x=><BranchScore key={x.branch} branch={x}/>):<div className="border rounded-xl p-4 text-sm text-[#8d8178]">هنوز شعبه فعال وجود ندارد.</div>}</div></section>
  </div>

  <h3 className="font-black text-lg mb-3">بخش‌های تنظیمات</h3><div className="grid md:grid-cols-2 2xl:grid-cols-3 gap-4">{cards.filter(x=>can(x[4])).map(([href,title,desc,Icon])=><Link href={href} key={href} className="card p-5 hover:-translate-y-0.5 transition-transform"><div className="flex items-start justify-between"><span className="w-11 h-11 rounded-xl bg-[#eee6dc] grid place-items-center"><Icon size={22}/></span><CheckCircle2 size={18} className="text-emerald-600"/></div><h3 className="font-black text-lg mt-4">{title}</h3><p className="text-sm text-[#8d8178] leading-6 mt-1">{desc}</p></Link>)}</div>
 </div>
}

function Metric({label,value,detail}:{label:string;value:string;detail:string}){return <div className="card p-4"><div className="text-sm text-[#8d8178]">{label}</div><b className="text-2xl block mt-1">{value}</b><div className="text-xs text-[#8d8178] mt-1">{detail}</div></div>}

function CheckRow({check}:{check:SetupCheck}){const done=check.status==="done";const warning=check.status==="warning";return <div className="border rounded-xl p-3 flex items-start gap-3"><div className="mt-0.5">{done?<CheckCircle2 size={19} className="text-emerald-600"/>:<CircleAlert size={19} className={warning?"text-amber-600":"text-red-600"}/>}</div><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2"><b className="text-sm">{check.title}</b><span className="badge">{done?"کامل":check.required?"ضروری":"پیشنهادی"}</span></div><p className="text-xs text-[#8d8178] leading-6 mt-1">{check.detail}</p></div>{!done&&<Link href={check.href} className="btn shrink-0">تکمیل</Link>}</div>}

function BranchScore({branch}:{branch:BranchReadiness}){return <div className="border rounded-xl p-3"><div className="flex items-center justify-between gap-3"><div><b>{branch.name}</b><div className="text-xs text-[#8d8178]">{branch.completed}/{branch.total} مورد ضروری</div></div><span className={`badge ${branch.blocking?"text-amber-700":"text-emerald-700"}`}>{branch.score}%</span></div><div className="h-2 rounded-full bg-[#eee6dc] overflow-hidden mt-3"><div className="h-full bg-emerald-600" style={{width:`${branch.score}%`}}/></div></div>}

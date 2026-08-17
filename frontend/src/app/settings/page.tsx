"use client";
import Link from "next/link";
import {Building2,Store,Armchair,ReceiptText,Boxes,Globe2,MessageSquare,UsersRound,CheckCircle2,AlertCircle} from "lucide-react";
import {useSettings} from "@/components/settings/settings-context";
const cards=[
 ["/settings/business","پروفایل کسب‌وکار","نام، نوع مجموعه، مدل استقرار و ماژول‌های فعال",Building2,"business.manage"],
 ["/settings/branches","شعب و صندوق‌ها","اطلاعات شعب، شماره تماس، صندوق‌های فروش",Store,"branches.manage"],
 ["/settings/dining","سالن و میزها","تعریف سالن، شماره میز و ظرفیت",Armchair,"settings.manage"],
 ["/settings/sales","فروش و مالی","مالیات، حق سرویس، صندوق و چاپ",ReceiptText,"settings.manage"],
 ["/settings/catalog","منو و موجودی","محصول، دسته، رسپی و انبار",Boxes,"inventory.manage"],
 ["/settings/online","سفارش آنلاین","QR، تحویل، ارسال، محدوده و درگاه",Globe2,"online_ordering.manage"],
 ["/settings/notifications","اطلاع‌رسانی","پیامک، Web Push و صف اعلان",MessageSquare,"notifications.manage"],
 ["/settings/team","تیم و دسترسی","ساخت کاربر، نقش، شعبه و Permission Matrix",UsersRound,"permissions.manage"],
] as const;
export default function SettingsHome(){const {data,can}=useSettings();if(!data)return null;const enabled=data.modules.filter(x=>x.enabled).length;return <div><div className="mb-5"><h2 className="text-3xl font-black">مرکز تنظیمات</h2><p className="text-[#8d8178] mt-1">تنظیمات روزمره کسب‌وکار از همین داشبورد انجام می‌شود؛ Django Admin برای پشتیبانی پلتفرم باقی می‌ماند.</p></div>
<div className="grid sm:grid-cols-3 gap-3 mb-5"><div className="card p-4"><div className="text-sm text-[#8d8178]">شعب فعال</div><b className="text-2xl">{data.branches.filter(b=>b.is_active).length}</b></div><div className="card p-4"><div className="text-sm text-[#8d8178]">ماژول فعال</div><b className="text-2xl">{enabled}</b></div><div className="card p-4"><div className="text-sm text-[#8d8178]">مدل استقرار</div><b className="text-xl">{data.business.deployment_type}</b></div></div>
<div className="grid md:grid-cols-2 2xl:grid-cols-3 gap-4">{cards.filter(x=>can(x[4])).map(([href,title,desc,Icon])=><Link href={href} key={href} className="card p-5 hover:-translate-y-0.5 transition-transform"><div className="flex items-start justify-between"><span className="w-11 h-11 rounded-xl bg-[#eee6dc] grid place-items-center"><Icon size={22}/></span><CheckCircle2 size={18} className="text-emerald-600"/></div><h3 className="font-black text-lg mt-4">{title}</h3><p className="text-sm text-[#8d8178] leading-6 mt-1">{desc}</p></Link>)}</div>
<div className="card p-4 mt-5 flex gap-3 items-start"><AlertCircle className="shrink-0 text-[#b9792d]"/><p className="text-sm leading-7">تغییرات حساس تنظیمات در Audit Log ثبت می‌شوند. Secretهای درگاه، پیامک و Push در لاگ ماسک می‌شوند و در پاسخ API نیز مقدار رمزنگاری‌شده افشا نمی‌شود.</p></div></div>}

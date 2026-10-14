"use client";

import Link from "next/link";
import {ClipboardList,RefreshCw} from "lucide-react";
import {useEffect,useState} from "react";
import {api} from "@/lib/api";
import {label} from "@/lib/i18n";

type KitchenStatus={station_id:number;station_name:string;status:"NEW"|"PREPARING"|"READY"|"DONE"};
type PaymentMethod="POS"|"CASH"|"CREDIT"|"WALLET"|"GIFT_CARD";
type Tender={method:PaymentMethod;amount:string;tendered_amount:string;reference_number:string;gift_card_code:string};
type Order={id:number;order_number:number;order_type:string;status:string;payment_status:string;tax_total:number|string;service_charge_total:number|string;grand_total:number|string;outstanding_amount:string;payments?:Array<{method:string;amount:number|string}>;kitchen_statuses?:KitchenStatus[]};
const kitchenLabels:Record<KitchenStatus["status"],string>={NEW:"در صف آماده‌سازی",PREPARING:"در حال آماده‌سازی",READY:"آماده برای تحویل",DONE:"تحویل شد"};
const kitchenClasses:Record<KitchenStatus["status"],string>={NEW:"bg-amber-50 text-amber-800",PREPARING:"bg-sky-50 text-sky-800",READY:"bg-emerald-50 text-emerald-800",DONE:"bg-[#eee6dc] text-[#766858]"};
const paymentLabels:Record<PaymentMethod,string>={POS:"کارت‌خوان",CASH:"نقدی",CREDIT:"اعتباری",WALLET:"کیف پول",GIFT_CARD:"کارت هدیه"};
const normalizeAmount=(value:string)=>value
 .replace(/[۰-۹]/g,digit=>String("۰۱۲۳۴۵۶۷۸۹".indexOf(digit)))
 .replace(/[٠-٩]/g,digit=>String("٠١٢٣٤٥٦٧٨٩".indexOf(digit)))
 .replace(/[٬,\s]/g,"");

export default function Orders(){
 const [rows,setRows]=useState<Order[]>([]),[msg,setMsg]=useState(""),[loading,setLoading]=useState(true),[error,setError]=useState(""),[refreshing,setRefreshing]=useState(false),[settlingOrder,setSettlingOrder]=useState<Order|null>(null),[tenders,setTenders]=useState<Tender[]>([]),[savingSettlement,setSavingSettlement]=useState(false);
 const load=async(manual=false)=>{
  if(manual)setRefreshing(true);
  try{setError("");setRows(await api<Order[]>("/orders/"))}
  catch(caught){setError(caught instanceof Error?caught.message:"دریافت سفارش‌ها انجام نشد.")}
  finally{setLoading(false);if(manual)setRefreshing(false)}
 };
 useEffect(()=>{void load();const interval=window.setInterval(()=>void load(),5000);return()=>window.clearInterval(interval)},[]);

 async function managerToken(permission:string){const pin=prompt("رمز مدیر:");if(!pin)throw new Error("عملیات لغو شد");const branches=await api<any[]>("/branches/");const x=await api<any>("/manager-override/",{method:"POST",body:JSON.stringify({pin,permission_code:permission,branch:branches[0]?.id})});return x.token}
 async function callWithOverride(path:string,permission:string,body:any){try{return await api(path,{method:"POST",body:JSON.stringify(body)})}catch(error:any){if(!String(error.message).includes("تأیید مدیر")&&!String(error.message).includes("نیازمند"))throw error;const token=await managerToken(permission);return api(path,{method:"POST",headers:{"X-Cafino-Override":token},body:JSON.stringify(body)})}}
 async function voidOrder(id:number){const reason=prompt("علت لغو سفارش؟","لغو توسط صندوق")||"لغو";if(!confirm("موجودی و همه پرداخت‌های سفارش برگشت داده شوند؟"))return;try{await callWithOverride(`/orders/${id}/cancel/`,"orders.void",{reason});setMsg("لغو سفارش ثبت شد.");void load()}catch(error:any){setMsg(error.message||"لغو سفارش انجام نشد.")}}
 async function refund(id:number,total:number){const amount=prompt("مبلغ برگشت وجه؟",String(total));if(!amount)return;const reason=prompt("علت برگشت وجه؟","مرجوعی یا اصلاح سفارش")||"برگشت وجه";try{await callWithOverride(`/orders/${id}/refund/`,"payments.refund",{amount:Number(amount),reason});setMsg("برگشت وجه ثبت شد.");void load()}catch(error:any){setMsg(error.message||"برگشت وجه انجام نشد.")}}
 async function printReceipt(id:number){
  // Open synchronously within the click to avoid popup blockers after the API request.
  const popup=window.open("","_blank","width=420,height=700");
  if(!popup){setMsg("مرورگر پنجره چاپ را مسدود کرده است. اجازه بازشدن پنجره را بدهید و دوباره تلاش کنید.");return}
  popup.document.write('<html lang="fa" dir="rtl"><head><meta charset="utf-8"><title>آماده‌سازی رسید</title></head><body style="font-family:Tahoma,sans-serif;padding:16px">در حال آماده‌سازی رسید…</body></html>');
  popup.document.close();
  try{
   // A read-only receipt payload does not create a printer record or a print job.
   const payload=await api<any>(`/orders/${id}/receipt-payload/`);
   if(popup.closed){setMsg("پنجره چاپ بسته شد.");return}
   const escapeHtml=(value:unknown)=>String(value??"").replace(/[&<>"']/g,char=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]||char));
   const money=(value:unknown)=>Number(value||0).toLocaleString("fa-IR");
   const items=Array.isArray(payload.items)?payload.items:[];
   const html=`<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><title>رسید سفارش ${escapeHtml(payload.order_number)}</title><style>@page{size:80mm auto;margin:3mm}body{font-family:Tahoma,Arial,sans-serif;direction:rtl;max-width:80mm;margin:auto;padding:6px;font-size:12px;color:#111}h2,h3{text-align:center;margin:8px 0}p{margin:6px 0}hr{border:0;border-top:1px dashed #555}.row{display:flex;justify-content:space-between;gap:6px;margin:7px 0}.total{font-size:16px;font-weight:bold}@media print{button{display:none!important}}</style></head><body><h2>${escapeHtml(payload.business)}</h2><h3>سفارش شماره ${escapeHtml(payload.order_number)}</h3><hr>${items.map((item:any)=>`<div class="row"><span>${escapeHtml(item.quantity)} × ${escapeHtml(item.name)}</span><span>${money(item.line_total)}</span></div>`).join("")}<hr><div class="row total"><span>مبلغ کل</span><span>${money(payload.grand_total)} ریال</span></div><button type="button" onclick="window.print()" style="width:100%;padding:12px;margin-top:16px">چاپ رسید</button></body></html>`;
   popup.document.open();popup.document.write(html);popup.document.close();
   popup.focus();popup.print();
   setMsg("رسید برای چاپ در مرورگر آماده شد. تأیید انجام چاپ با خود مرورگر است.");
  }catch(error:any){
   if(!popup.closed){popup.document.body.textContent="آماده‌سازی رسید ناموفق بود. پنجره را ببندید و دوباره تلاش کنید.";}
   setMsg(error.message||"آماده‌سازی رسید انجام نشد.");
  }
 }
 const openSettlement=(order:Order)=>{setSettlingOrder(order);setTenders([{method:"POS",amount:order.outstanding_amount||String(order.grand_total),tendered_amount:order.outstanding_amount||String(order.grand_total),reference_number:"",gift_card_code:""}]);setMsg("")};
 const updateTender=(index:number,changes:Partial<Tender>)=>setTenders(current=>current.map((tender,tenderIndex)=>tenderIndex===index?{...tender,...changes}:tender));
 const addTender=()=>setTenders(current=>[...current,{method:"CASH",amount:"",tendered_amount:"",reference_number:"",gift_card_code:""}]);
 const removeTender=(index:number)=>setTenders(current=>current.length===1?current:current.filter((_,tenderIndex)=>tenderIndex!==index));
 const submitSettlement=async()=>{
  if(!settlingOrder)return;
  const normalizedTenders=tenders.map(tender=>({
   ...tender,
   amount:normalizeAmount(tender.amount),
   tendered_amount:normalizeAmount(tender.method==="CASH"?(tender.tendered_amount||tender.amount):tender.amount),
  }));
  if(normalizedTenders.some(tender=>!/^\d+$/.test(tender.amount)||Number(tender.amount)<=0)){setMsg("مبلغ هر روش پرداخت را به‌صورت عدد صحیح و مثبت وارد کنید.");return}
  if(normalizedTenders.some(tender=>tender.method==="CASH"&&(!/^\d+$/.test(tender.tendered_amount)||Number(tender.tendered_amount)<Number(tender.amount)))){setMsg("وجه دریافتی نقدی نمی‌تواند کمتر از مبلغ نقدی باشد.");return}
  if(tenders.some(tender=>tender.method==="GIFT_CARD"&&!tender.gift_card_code.trim())){setMsg("کد کارت هدیه را وارد کنید.");return}
  setSavingSettlement(true);setMsg("");
  try{await api(`/orders/${settlingOrder.id}/settle/`,{method:"POST",body:JSON.stringify({require_full:true,payments:normalizedTenders.map(tender=>({method:tender.method,amount:tender.amount,tendered_amount:tender.tendered_amount,reference_number:tender.reference_number,gift_card_code:tender.gift_card_code}))})});setSettlingOrder(null);setTenders([]);setMsg(`تسویهٔ کامل سفارش #${settlingOrder.order_number} ثبت شد.`);await load()}catch(error:any){setMsg(error.message||"تسویهٔ سفارش انجام نشد.")}finally{setSavingSettlement(false)}
 };

 if(loading)return <div className="card p-8 text-center text-[#8d8178]">در حال دریافت سفارش‌ها…</div>;
 return <div>
  <div className="mb-5 flex flex-wrap items-end justify-between gap-3"><div><h1 className="mb-2 text-3xl font-black">سفارش‌ها، پرداخت و چاپ</h1><p className="text-[#8d8178]">وضعیت آماده‌سازی هر سفارش از آشپزخانه، هر ۵ ثانیه خودکار به‌روز می‌شود.</p></div><button className="btn inline-flex items-center gap-2" onClick={()=>void load(true)} disabled={refreshing}><RefreshCw className={refreshing?"h-4 w-4 animate-spin":"h-4 w-4"} aria-hidden="true"/>تازه‌سازی</button></div>
  {msg&&<div role="status" className="card mb-4 p-3">{msg}</div>}
  {error&&<div className="card mb-4 border border-red-200 p-3 text-red-700">{error}</div>}
  {settlingOrder&&<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/35 p-4" role="dialog" aria-modal="true" aria-labelledby="settlement-title"><section className="card max-h-[90vh] w-full max-w-2xl overflow-y-auto p-5 shadow-xl"><div className="flex items-start justify-between gap-3"><div><h2 id="settlement-title" className="text-xl font-black">تسویهٔ سفارش #{settlingOrder.order_number}</h2><p className="mt-1 text-sm text-[#8d8178]">مبلغ قابل پرداخت: <b>{Number(settlingOrder.outstanding_amount).toLocaleString("fa-IR")} ریال</b></p></div><button type="button" className="btn" onClick={()=>{setSettlingOrder(null);setTenders([])}} disabled={savingSettlement}>انصراف</button></div><div className="mt-5 space-y-3">{tenders.map((tender,index)=><div className="rounded-xl border border-[#e9dfd3] p-3" key={index}><div className="grid gap-2 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto]"><label className="text-sm">روش پرداخت<select className="btn mt-1 w-full" value={tender.method} onChange={event=>updateTender(index,{method:event.target.value as PaymentMethod})}>{(Object.keys(paymentLabels) as PaymentMethod[]).map(method=><option value={method} key={method}>{paymentLabels[method]}</option>)}</select></label><label className="text-sm">مبلغ به ریال<input className="btn mt-1 w-full" inputMode="numeric" placeholder="مبلغ پرداخت" value={tender.amount} onChange={event=>updateTender(index,{amount:event.target.value})}/></label><button type="button" className="btn self-end text-red-700" onClick={()=>removeTender(index)} disabled={tenders.length===1||savingSettlement}>حذف</button></div>{tender.method==="CASH"&&<label className="mt-2 block text-sm">وجه دریافت‌شده<input className="btn mt-1 w-full" inputMode="numeric" placeholder="برای محاسبهٔ باقی‌مانده" value={tender.tendered_amount} onChange={event=>updateTender(index,{tendered_amount:event.target.value})}/></label>}{tender.method==="GIFT_CARD"&&<label className="mt-2 block text-sm">کد کارت هدیه<input className="btn mt-1 w-full" placeholder="کد کارت هدیه" value={tender.gift_card_code} onChange={event=>updateTender(index,{gift_card_code:event.target.value})}/></label>}{tender.method==="POS"&&<label className="mt-2 block text-sm">شمارهٔ پیگیری (اختیاری)<input className="btn mt-1 w-full" inputMode="numeric" placeholder="شمارهٔ پیگیری کارت‌خوان" value={tender.reference_number} onChange={event=>updateTender(index,{reference_number:event.target.value})}/></label>}</div>)}</div><div className="mt-4 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end"><button type="button" className="btn" onClick={addTender} disabled={savingSettlement}>افزودن روش پرداخت</button><button type="button" className="btn btn-primary" onClick={()=>void submitSettlement()} disabled={savingSettlement}>{savingSettlement?"در حال ثبت تسویه…":"ثبت تسویهٔ کامل"}</button></div><p className="mt-3 text-xs text-[#8d8178]">جمع روش‌های پرداخت باید دقیقاً با مبلغ قابل پرداخت برابر باشد؛ سامانه پیش از ثبت آن را کنترل می‌کند.</p></section></div>}
  {rows.length===0?<section className="card flex min-h-56 flex-col items-center justify-center p-8 text-center" aria-live="polite"><div className="mb-4 rounded-full bg-[#eee6dc] p-4 text-[#b9792d]"><ClipboardList className="h-8 w-8" aria-hidden="true"/></div><h2 className="text-xl font-black">هنوز سفارشی ثبت نشده است</h2><p className="mt-2 max-w-md leading-7 text-[#8d8178]">برای آغاز فروش، یک سفارش جدید ثبت کنید. سفارش‌های ثبت‌شده در این بخش برای پیگیری، چاپ و تسویه نمایش داده می‌شوند.</p><Link href="/pos" className="btn btn-primary mt-5">ثبت سفارش جدید</Link></section>:<div className="card overflow-x-auto"><table className="w-full min-w-[1100px]"><thead className="bg-[#eee6dc]"><tr><th className="p-3 text-right">شماره</th><th className="text-right">نوع</th><th className="text-right">وضعیت سفارش</th><th className="text-right">آماده‌سازی</th><th className="text-right">پرداخت</th><th className="text-right">مالیات/سرویس</th><th className="text-right">مبلغ</th><th></th></tr></thead><tbody>{rows.map(order=><tr className="border-t" key={order.id}><td className="p-3 font-bold">#{order.order_number}</td><td>{label(order.order_type)}</td><td>{label(order.status)}</td><td>{order.kitchen_statuses?.length?<div className="flex flex-wrap gap-1">{order.kitchen_statuses.map(ticket=><span key={ticket.station_id} className={`rounded-full px-2 py-1 text-xs font-bold ${kitchenClasses[ticket.status]}`}>{ticket.station_name}: {kitchenLabels[ticket.status]}</span>)}</div>:<span className="text-sm text-[#8d8178]">بدون تیکت آشپزخانه</span>}</td><td><div>{label(order.payment_status)}</div><div className="text-xs">{order.payments?.map(payment=>`${label(payment.method)}: ${Number(payment.amount).toLocaleString("fa-IR")}`).join(" + ")}</div></td><td>{Number(order.tax_total||0).toLocaleString("fa-IR")} / {Number(order.service_charge_total||0).toLocaleString("fa-IR")}</td><td>{Number(order.grand_total).toLocaleString("fa-IR")}</td><td><div className="flex flex-wrap gap-2 p-2">{order.status!=="CANCELLED"&&order.status!=="COMPLETED"&&order.payment_status!=="PAID"&&order.payment_status!=="REFUNDED"&&<button className="btn btn-primary" onClick={()=>openSettlement(order)}>تسویه</button>}<button className="btn" onClick={()=>void printReceipt(order.id)}>چاپ</button>{order.status!=="CANCELLED"&&order.status!=="COMPLETED"&&<button className="btn" onClick={()=>void voidOrder(order.id)}>لغو سفارش</button>}{order.status==="COMPLETED"&&order.payment_status!=="REFUNDED"&&<button className="btn" onClick={()=>void refund(order.id,Number(order.grand_total))}>برگشت وجه</button>}</div></td></tr>)}</tbody></table></div>}
 </div>;
}

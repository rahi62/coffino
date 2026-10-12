"use client";
import {useEffect,useMemo,useRef,useState} from "react";
import FormDialog from "@/components/form-dialog";
import {api} from "@/lib/api";

type Product={id:number;name:string;price:string;category:number|null;category_name?:string};
type Category={id:number;name:string};
type Tender={method:string;amount:string;tendered_amount?:string;payer_label?:string;gift_card_code?:string;bank_account?:string};
type Table={id:number;number:string;status:"FREE"|"OCCUPIED"|"RESERVED";capacity:number};
type Pager={id:number;number:string;status:"AVAILABLE"|"ASSIGNED"|"DISABLED"};
type BankAccount={id:number;branch:number;display_name:string;is_active:boolean};
const normalizeCustomerSearch=(value:string)=>value.trim().toLocaleLowerCase("fa").replace(/[۰-۹]/g,digit=>"۰۱۲۳۴۵۶۷۸۹".indexOf(digit).toString()).replace(/[٠-٩]/g,digit=>"٠١٢٣٤٥٦٧٨٩".indexOf(digit).toString());

export default function POS(){
  const [products,setProducts]=useState<Product[]>([]),[categories,setCategories]=useState<Category[]>([]),[tables,setTables]=useState<Table[]>([]),[branches,setBranches]=useState<any[]>([]),[zones,setZones]=useState<any[]>([]),[pagers,setPagers]=useState<Pager[]>([]),[customers,setCustomers]=useState<any[]>([]),[bankAccounts,setBankAccounts]=useState<BankAccount[]>([]);
  const [category,setCategory]=useState<number|null>(null),[cart,setCart]=useState<Record<number,number>>({});
  const [orderType,setOrderType]=useState("TAKEAWAY"),[table,setTable]=useState(""),[deliveryZone,setDeliveryZone]=useState(""),[deliveryAddress,setDeliveryAddress]=useState(""),[readyNotificationMethod,setReadyNotificationMethod]=useState("SMS"),[pagerId,setPagerId]=useState("");
  const [customerName,setCustomerName]=useState(""),[customerPhone,setCustomerPhone]=useState(""),[customerQuery,setCustomerQuery]=useState(""),[message,setMessage]=useState(""),[busy,setBusy]=useState(false);
  const [customerDialog,setCustomerDialog]=useState(false),[checkoutDialog,setCheckoutDialog]=useState(false),[preparingCheckout,setPreparingCheckout]=useState(false);
  const [discountCode,setDiscountCode]=useState(""),[manualPercent,setManualPercent]=useState(""),[manualAmount,setManualAmount]=useState(""),[managerPin,setManagerPin]=useState("");
  const [preview,setPreview]=useState<any>(null),[deferPayment,setDeferPayment]=useState(false),[mixed,setMixed]=useState(false),[singleMethod,setSingleMethod]=useState("POS"),[singleGiftCode,setSingleGiftCode]=useState(""),[singleBankAccount,setSingleBankAccount]=useState(""),[tenders,setTenders]=useState<Tender[]>([{method:"POS",amount:"",payer_label:"نفر ۱"}]),[splitGuests,setSplitGuests]=useState("2");
  const checkoutKey=useRef("");
  const [cartOpen,setCartOpen]=useState(false);
  const [initialLoading,setInitialLoading]=useState(true);
  const [initialError,setInitialError]=useState("");

  function load(){setInitialLoading(true);setInitialError("");Promise.all([api<Product[]>("/products/"),api<Category[]>("/categories/"),api<Table[]>("/tables/"),api<any[]>("/branches/"),api<any[]>("/delivery-zones/"),api<Pager[]>("/pagers/"),api<any[]>("/customers/"),api<BankAccount[]>("/bank-accounts/")]).then(([p,c,t,b,z,pg,cu,accounts])=>{setProducts(p);setCategories(c);setTables(t);setBranches(b);setZones(z);setPagers(pg);setCustomers(cu.filter(customer=>!customer.is_walk_in));setBankAccounts(accounts.filter(account=>account.is_active));if(z[0]&&!deliveryZone)setDeliveryZone(z[0].code)}).catch(e=>{setInitialError(e instanceof Error?e.message:"دریافت اطلاعات فروش ناموفق بود.");}).finally(()=>setInitialLoading(false))}
  useEffect(load,[]);
  const shown=category?products.filter(x=>x.category===category):products;
  const cartCount=Object.values(cart).reduce((a,b)=>a+Number(b||0),0);
  const subtotal=useMemo(()=>products.reduce((sum,p)=>sum+(cart[p.id]||0)*Number(p.price),0),[cart,products]);
  const manualPreview=useMemo(()=>Math.min(subtotal,Number(manualAmount||0)||subtotal*(Number(manualPercent||0)/100)),[subtotal,manualAmount,manualPercent]);
  const tenderSum=useMemo(()=>tenders.reduce((s,x)=>s+Number(x.amount||0),0),[tenders]);
  const branchBankAccounts=useMemo(()=>bankAccounts.filter(account=>account.branch===branches[0]?.id),[bankAccounts,branches]);
  const matchingCustomers=useMemo(()=>{const query=normalizeCustomerSearch(customerQuery);if(!query)return [];return customers.filter(customer=>normalizeCustomerSearch(String(customer.name||"")).includes(query)||normalizeCustomerSearch(String(customer.phone||"")).includes(query)).slice(0,6)},[customers,customerQuery]);

  function invalidate(){setPreview(null);checkoutKey.current=""}
  function inc(id:number){invalidate();setCart(x=>({...x,[id]:(x[id]||0)+1}))}
  function dec(id:number){invalidate();setCart(x=>({...x,[id]:Math.max(0,(x[id]||0)-1)}))}
  const itemsPayload=()=>Object.entries(cart).filter(([,q])=>Number(q)>0).map(([id,q])=>({product:Number(id),quantity:Number(q)}));

  async function overrideToken(branchId:number){
    const needs=Number(manualAmount||0)>0||Number(manualPercent||0)>0||!!discountCode;
    if(!needs||!managerPin)return "";
    const ov=await api<any>("/manager-override/",{method:"POST",body:JSON.stringify({pin:managerPin,permission_code:"discount.manual",branch:branchId})});
    return ov.token as string;
  }

  async function calculatePreview(){
    const items=itemsPayload();if(!items.length)throw new Error("حداقل یک آیتم انتخاب کن");
    const br=branches[0];if(!br)throw new Error("شعبه‌ای تعریف نشده است");
    const token=await overrideToken(br.id);
    const manual=(Number(manualAmount||0)>0||Number(manualPercent||0)>0)?{amount:Number(manualAmount||0),percent:Number(manualPercent||0)}:null;
    const d=await api<any>("/checkout/preview/",{method:"POST",headers:token?{"X-Cafino-Override":token}:{},body:JSON.stringify({branch:br.id,items,order_type:orderType,discount_code:discountCode||null,manual_discount:manual,delivery:orderType==="DELIVERY"?{zone_code:deliveryZone,address:deliveryAddress,recipient_name:customerName,phone:customerPhone}:null,zone_code:orderType==="DELIVERY"?deliveryZone:null})});
    setPreview(d);
    if(mixed&&tenders.length===1&&!Number(tenders[0].amount))setTenders([{...tenders[0],amount:String(d.grand_total)}]);
    return {d,token};
  }

  async function checkout(){
    if(orderType==="DINE_IN"&&!table){setMessage("برای سفارش داخل سالن، میز را انتخاب کنید.");return}
    if(orderType==="TAKEAWAY"&&readyNotificationMethod==="SMS"&&!customerPhone.trim()){setMessage("برای اطلاع‌رسانی پیامکی، شماره همراه مشتری را وارد کنید.");return}
    if(orderType==="TAKEAWAY"&&readyNotificationMethod==="PAGER"&&!pagerId){setMessage("برای فراخوانی پیجر، یک پیجر آزاد را انتخاب کنید.");return}
    setBusy(true);setMessage("");
    try{
      const {d,token}=await calculatePreview();
      let payments:any[]=[];
      if(!deferPayment&&mixed){
        if(Math.round(tenderSum)!==Math.round(Number(d.grand_total)))throw new Error(`جمع روش‌های پرداخت باید دقیقاً ${Number(d.grand_total).toLocaleString("fa-IR")} ریال باشد`);
        payments=tenders.map(x=>({method:x.method,amount:String(Number(x.amount)),tendered_amount:x.method==="CASH"?String(Number(x.tendered_amount||x.amount)):String(Number(x.amount)),payer_label:x.payer_label||"",gift_card_code:x.gift_card_code||"",bank_account:x.method==="POS"&&x.bank_account?Number(x.bank_account):null}));
      }else if(!deferPayment){
        payments=[{method:singleMethod,amount:String(Number(d.grand_total)),tendered_amount:String(Number(d.grand_total)),payer_label:"",gift_card_code:singleMethod==="GIFT_CARD"?singleGiftCode:"",bank_account:singleMethod==="POS"&&singleBankAccount?Number(singleBankAccount):null}];
      }
      const br=branches[0];
      const manual=(Number(manualAmount||0)>0||Number(manualPercent||0)>0)?{amount:Number(manualAmount||0),percent:Number(manualPercent||0),reason:"تخفیف دستی صندوق"}:null;
      if(!checkoutKey.current)checkoutKey.current=(globalThis.crypto?.randomUUID?.()||`${Date.now()}-${Math.random()}`);
      const order=await api<any>("/checkout/",{method:"POST",headers:{...(token?{"X-Cafino-Override":token}:{}),"Idempotency-Key":checkoutKey.current},body:JSON.stringify({
        branch:br.id,items:itemsPayload(),order_type:orderType,payments:deferPayment?null:payments,defer_payment:deferPayment,
        table:orderType==="DINE_IN"?Number(table):null,customer_name:customerName,customer_phone:customerPhone,ready_notification_method:orderType==="TAKEAWAY"?readyNotificationMethod:"NONE",pager_id:orderType==="TAKEAWAY"&&readyNotificationMethod==="PAGER"?Number(pagerId):null,
        discount_code:discountCode||null,manual_discount:manual,
        delivery:orderType==="DELIVERY"?{zone_code:deliveryZone,address:deliveryAddress,recipient_name:customerName,phone:customerPhone}:null
      })});
      setCart({});setCartOpen(false);setCustomerName("");setCustomerPhone("");setCustomerQuery("");setPagerId("");setReadyNotificationMethod("SMS");setDiscountCode("");setManualAmount("");setManualPercent("");setManagerPin("");setSingleGiftCode("");setSingleBankAccount("");setPreview(null);setTenders([{method:"POS",amount:"",payer_label:"نفر ۱"}]);checkoutKey.current="";load();
      setMessage(`✓ سفارش ${order.order_number} ثبت شد — مبلغ نهایی ${Number(order.grand_total).toLocaleString("fa-IR")} ریال`);
    }catch(e:any){setMessage(`خطا: ${e?.message||"نامشخص"}`)}finally{setBusy(false)}
  }

  async function prepareCheckout(){
    if(orderType==="DINE_IN"&&!table){setMessage("برای سفارش داخل سالن، میز را انتخاب کنید.");return}
    if(orderType==="TAKEAWAY"&&readyNotificationMethod==="SMS"&&!customerPhone.trim()){setMessage("برای اطلاع‌رسانی پیامکی، شماره همراه مشتری را وارد کنید.");setCustomerDialog(true);return}
    if(orderType==="TAKEAWAY"&&readyNotificationMethod==="PAGER"&&!pagerId){setMessage("برای فراخوانی پیجر، یک پیجر آزاد را انتخاب کنید.");return}
    setPreparingCheckout(true);setMessage("");
    try{await calculatePreview();setCheckoutDialog(true)}catch(error:any){setMessage(error.message||"محاسبهٔ مبلغ نهایی انجام نشد.")}finally{setPreparingCheckout(false)}
  }

  function addTender(){setTenders(x=>[...x,{method:"CASH",amount:"",payer_label:`نفر ${x.length+1}`}])}
  function equalSplit(){
    if(!preview){setMessage("ابتدا مبلغ نهایی را محاسبه کن");return}
    const count=Math.max(2,Math.min(20,Number(splitGuests||2)));const total=Math.round(Number(preview.grand_total));const base=Math.floor(total/count);const rem=total-base*count;
    setMixed(true);setTenders(Array.from({length:count},(_,i)=>({method:"POS",amount:String(base+(i===0?rem:0)),payer_label:`نفر ${i+1}`})));
  }
  if(initialLoading)return <div role="status" className="card p-5">در حال دریافت محصولات و اطلاعات فروش…</div>;
  if(initialError)return <section role="alert" className="card border-red-200 p-5"><h1 className="text-xl font-black">فروش در دسترس نیست</h1><p className="mt-2 text-sm text-red-800">{initialError}</p><button type="button" className="btn mt-4 min-h-11" onClick={load}>تلاش دوباره</button></section>;
  return <div className="pb-24 md:flex md:h-[calc(100dvh-2.5rem)] md:flex-col md:pb-0 xl:h-[calc(100dvh-3rem)]">
    <div className="mb-4 flex shrink-0 flex-wrap items-end justify-between gap-3 md:mb-3">
      <div><h1 className="text-2xl font-black md:text-3xl">فروش جدید</h1><p className="hidden text-[#8d8178] sm:block">پیش‌نمایش قطعی سامانه ← مالیات و سرویس ← پرداخت ترکیبی ← آماده‌سازی</p></div>
      <div className="flex flex-wrap gap-2"><select className="btn" value={orderType} onChange={e=>{setOrderType(e.target.value);setTable("");invalidate()}}><option value="TAKEAWAY">بیرون‌بر</option><option value="DINE_IN">داخل سالن</option><option value="PICKUP">تحویل حضوری</option><option value="DELIVERY">ارسال</option></select>
      {orderType==="DINE_IN"&&<select className="btn" value={table} onChange={e=>setTable(e.target.value)}><option value="">انتخاب میز...</option>{tables.filter(t=>t.status!=="RESERVED").map(t=><option key={t.id} value={t.id}>میز {t.number} — {t.status==="FREE"?"آزاد":"مشغول؛ افزودن سفارش"}</option>)}</select>}{orderType==="DELIVERY"&&<select className="btn" value={deliveryZone} onChange={e=>{setDeliveryZone(e.target.value);invalidate()}}><option value="">منطقه ارسال...</option>{zones.map(z=><option key={z.id} value={z.code}>{z.name}</option>)}</select>}</div>
    </div>
    {message&&<div className="card mb-3 shrink-0 p-3">{message}</div>}
    <div className="grid grid-cols-1 gap-3 md:min-h-0 md:flex-1 md:grid-cols-[minmax(0,1fr)_minmax(320px,360px)] md:grid-rows-[auto_minmax(0,1fr)] xl:grid-cols-[140px_minmax(0,1fr)_minmax(340px,420px)] xl:grid-rows-[minmax(0,1fr)] xl:gap-4">
      <div className="card flex gap-2 overflow-x-auto p-2 md:col-span-2 xl:col-span-1 xl:block xl:min-h-0 xl:space-y-2 xl:overflow-y-auto xl:overflow-x-visible xl:p-3" role="tablist" aria-label="دسته‌بندی منو"><button role="tab" aria-selected={category===null} className={`btn shrink-0 xl:w-full ${category===null?"btn-primary":""}`} onClick={()=>setCategory(null)}>همه</button>{categories.map(c=><button role="tab" aria-selected={category===c.id} className={`btn shrink-0 xl:w-full ${category===c.id?"btn-primary":""}`} key={c.id} onClick={()=>setCategory(c.id)}>{c.name}</button>)}</div>
      <div className="grid grid-cols-2 content-start gap-3 md:min-h-0 md:overflow-y-auto md:pb-1 min-[900px]:grid-cols-3 xl:grid-cols-3 2xl:grid-cols-4">{shown.map(p=><button key={p.id} className="card relative min-h-[104px] p-3 text-right transition active:scale-[.98] md:p-4 md:hover:-translate-y-1" onClick={()=>inc(p.id)}>{cart[p.id]>0&&<span className="absolute left-2 top-2 grid min-w-7 place-items-center rounded-full bg-[#b9792d] px-1.5 text-sm font-black text-white">{Number(cart[p.id]).toLocaleString("fa-IR")}</span>}<div className="font-bold text-base md:text-lg">{p.name}</div><div className="mt-1 text-xs text-[#8d8178]">{p.category_name||"بدون دسته"}</div><div className="mt-3 font-bold text-[#b9792d] md:mt-4">{Number(p.price).toLocaleString("fa-IR")} ریال</div></button>)}</div>
      {cartOpen&&<button type="button" aria-label="بستن سبد" className="fixed inset-0 z-30 h-full w-full cursor-default bg-black/45 md:hidden" onClick={()=>setCartOpen(false)}/>}
      <div className={`card p-4 ${cartOpen?"fixed inset-x-0 bottom-0 z-40 max-h-[90vh] overflow-y-auto !rounded-b-none !rounded-t-3xl shadow-2xl":"hidden"} md:static md:z-auto md:block md:max-h-none md:min-h-0 md:overflow-y-auto md:!rounded-[18px] md:shadow-none`} role={cartOpen?"dialog":undefined} aria-label="سبد سفارش">
        <div className="mb-3 flex items-start justify-between gap-2"><div><h2 className="text-xl font-black">سفارش جاری</h2><p className="mt-1 text-xs text-[#8d8178]">{customerName||customerPhone?`${customerName||"مشتری"}${customerPhone?` · ${customerPhone}`:""}`:"مشتری و اطلاعات تحویل هنوز ثبت نشده است."}</p></div><div className="flex gap-2"><button type="button" className="btn text-sm" onClick={()=>setCustomerDialog(true)}>مشتری و تحویل</button><button type="button" aria-label="بستن سبد" className="btn text-sm md:hidden" onClick={()=>setCartOpen(false)}>✕</button></div></div>{orderType==="TAKEAWAY"&&<div className="mb-3 rounded-xl bg-[#eee6dc] p-3"><div className="mb-2 text-sm font-bold">اطلاع‌رسانی آماده‌شدن سفارش</div><div className="grid gap-2 sm:grid-cols-2"><select className="btn w-full" value={readyNotificationMethod} onChange={e=>{setReadyNotificationMethod(e.target.value);setPagerId("")}}><option value="SMS">پیامک به مشتری</option><option value="PAGER">فراخوانی پیجر</option><option value="NONE">بدون اعلان</option></select>{readyNotificationMethod==="PAGER"&&<select className="btn w-full" value={pagerId} onChange={e=>setPagerId(e.target.value)}><option value="">انتخاب پیجر آزاد…</option>{pagers.filter(pager=>pager.status==="AVAILABLE").map(pager=><option key={pager.id} value={pager.id}>پیجر {pager.number}</option>)}</select>}</div><p className="mt-2 text-xs text-[#8d8178]">پس از آماده‌شدن همهٔ آیتم‌ها، پیامک یا فرمان فراخوانی پیجر در پس‌زمینه ارسال و وضعیت آن ثبت می‌شود.</p></div>}
        <div className="min-h-44 space-y-2 md:max-h-[28vh] md:overflow-auto">{products.filter(p=>cart[p.id]).map(p=><div key={p.id} className="flex justify-between items-center border-b pb-2"><div><b>{p.name}</b><div className="text-xs text-[#8d8178]">{(Number(p.price)*(cart[p.id]||0)).toLocaleString("fa-IR")}</div></div><div className="flex items-center gap-2"><button className="btn" onClick={()=>dec(p.id)}>−</button><b>{cart[p.id]}</b><button className="btn" onClick={()=>inc(p.id)}>+</button></div></div>)}</div>
        <div className="border-t pt-3 mt-3 space-y-2"><input className="border rounded-xl p-2 w-full" placeholder="کد تخفیف" value={discountCode} onChange={e=>{setDiscountCode(e.target.value);invalidate()}}/><div className="grid grid-cols-2 gap-2"><input className="border rounded-xl p-2" placeholder="تخفیف %" value={manualPercent} onChange={e=>{setManualPercent(e.target.value);invalidate()}}/><input className="border rounded-xl p-2" placeholder="تخفیف مبلغ" value={manualAmount} onChange={e=>{setManualAmount(e.target.value);invalidate()}}/></div>{(manualPreview>0||discountCode)&&<input type="password" inputMode="numeric" className="border rounded-xl p-2 w-full" placeholder="رمز مدیر در صورت نیاز" value={managerPin} onChange={e=>setManagerPin(e.target.value)}/>}</div>
        <button className="btn w-full mt-3" onClick={()=>calculatePreview().catch(e=>setMessage(e.message))}>محاسبه مبلغ نهایی</button>
        <div className="mt-3 text-sm space-y-1"><div className="flex justify-between"><span>جمع منو</span><b>{subtotal.toLocaleString("fa-IR")}</b></div>{preview&&<><div className="flex justify-between"><span>تخفیف</span><b>-{Number(preview.discount_total).toLocaleString("fa-IR")}</b></div><div className="flex justify-between"><span>حق سرویس</span><b>{Number(preview.service_charge_total).toLocaleString("fa-IR")}</b></div><div className="flex justify-between"><span>مالیات</span><b>{Number(preview.tax_total).toLocaleString("fa-IR")}</b></div><div className="flex justify-between text-xl font-black"><span>نهایی</span><span>{Number(preview.grand_total).toLocaleString("fa-IR")} ریال</span></div></>}</div>
        <div className="border-t mt-3 pt-3">{orderType==="DINE_IN"&&<label className="flex gap-2 items-center mb-2"><input type="checkbox" checked={deferPayment} onChange={e=>setDeferPayment(e.target.checked)}/> ارسال به آماده‌سازی و پرداخت در پایان سرویس</label>}<label className={`flex gap-2 items-center mb-2 ${deferPayment?"opacity-40":""}`}><input disabled={deferPayment} type="checkbox" checked={mixed} onChange={e=>setMixed(e.target.checked)}/> تقسیم / پرداخت ترکیبی</label>
        {deferPayment?<div className="bg-[#eee6dc] rounded-xl p-3 text-sm">سفارش بدون پرداخت ثبت می‌شود و بعداً از تقسیم صورتحساب یا تسویه سفارش پرداخت خواهد شد.</div>:!mixed?<div className="space-y-2"><select className="btn w-full" value={singleMethod} onChange={e=>{setSingleMethod(e.target.value);setSingleBankAccount("")}}><option value="POS">کارتخوان</option><option value="CASH">نقدی</option><option value="CREDIT">اعتباری</option><option value="WALLET">کیف پول</option><option value="GIFT_CARD">کارت هدیه</option></select>{singleMethod==="POS"&&<select className="btn w-full" value={singleBankAccount} onChange={e=>setSingleBankAccount(e.target.value)}><option value="">کارت‌خوان یا حساب را انتخاب کنید (اختیاری)</option>{branchBankAccounts.map(account=><option key={account.id} value={account.id}>{account.display_name}</option>)}</select>}{singleMethod==="GIFT_CARD"&&<input className="border rounded-xl p-2 w-full" placeholder="کد کارت هدیه" value={singleGiftCode} onChange={e=>setSingleGiftCode(e.target.value)}/>}</div>:<div className="space-y-2">
          <div className="flex gap-2"><input className="border rounded-xl p-2 w-24" value={splitGuests} onChange={e=>setSplitGuests(e.target.value)} placeholder="نفر"/><button className="btn" onClick={equalSplit}>تقسیم مساوی</button></div>
          {tenders.map((t,i)=><div className="grid grid-cols-2 gap-2 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_minmax(0,1fr)_42px]" key={i}><input className="border rounded-xl p-2 min-w-0" placeholder="پرداخت‌کننده" value={t.payer_label||""} onChange={e=>setTenders(x=>x.map((z,j)=>j===i?{...z,payer_label:e.target.value}:z))}/><select className="btn min-w-0" value={t.method} onChange={e=>setTenders(x=>x.map((z,j)=>j===i?{...z,method:e.target.value,bank_account:""}:z))}><option value="POS">کارتخوان</option><option value="CASH">نقدی</option><option value="CREDIT">اعتباری</option><option value="WALLET">کیف پول</option><option value="GIFT_CARD">کارت هدیه</option></select><input className="border rounded-xl p-2 min-w-0" placeholder={t.method==="GIFT_CARD"?"مبلغ؛ کد را پایین وارد کن":"مبلغ"} value={t.amount} onChange={e=>setTenders(x=>x.map((z,j)=>j===i?{...z,amount:e.target.value}:z))}/><button className="btn" onClick={()=>setTenders(x=>x.filter((_,j)=>j!==i))}>×</button>{t.method==="POS"&&<select className="btn min-w-0 col-span-full" value={t.bank_account||""} onChange={e=>setTenders(x=>x.map((z,j)=>j===i?{...z,bank_account:e.target.value}:z))}><option value="">کارت‌خوان یا حساب مشخص نشده است</option>{branchBankAccounts.map(account=><option key={account.id} value={account.id}>{account.display_name}</option>)}</select>}{t.method==="GIFT_CARD"&&<input className="border rounded-xl p-2 min-w-0 col-span-full" placeholder="کد کارت هدیه" value={t.gift_card_code||""} onChange={e=>setTenders(x=>x.map((z,j)=>j===i?{...z,gift_card_code:e.target.value}:z))}/>}</div>)}
          <button className="btn" onClick={addTender}>+ روش پرداخت</button><div className="text-sm">جمع پرداخت‌ها: <b>{tenderSum.toLocaleString("fa-IR")}</b></div></div>}</div>
        <div className="sticky -bottom-4 z-10 -mx-4 -mb-4 mt-3 border-t border-[#eadfd3] bg-[#fffdf9] px-4 pb-[max(1rem,env(safe-area-inset-bottom))] pt-3"><button disabled={busy||preparingCheckout} onClick={prepareCheckout} className="btn btn-primary w-full text-lg disabled:opacity-50">{busy||preparingCheckout?"در حال بررسی…":"بررسی و تأیید سفارش"}</button></div>
      </div>
    </div>
    {!cartOpen&&<div className="fixed inset-x-0 bottom-0 z-20 border-t border-[#eadfd3] bg-[#fffdf9]/95 p-3 pb-[max(.75rem,env(safe-area-inset-bottom))] backdrop-blur md:hidden"><button type="button" className="btn btn-primary flex w-full items-center justify-between text-base" onClick={()=>setCartOpen(true)}><span>مشاهده سبد · {cartCount.toLocaleString("fa-IR")} آیتم</span><b>{subtotal.toLocaleString("fa-IR")} ریال</b></button></div>}
    <FormDialog open={customerDialog} onClose={()=>setCustomerDialog(false)} closeDisabled={busy} width="sm" title="مشتری و اطلاعات تحویل" description="اطلاعات این سفارش را یک‌بار وارد کنید؛ برای باشگاه مشتریان و اطلاع‌رسانی آماده‌شدن استفاده می‌شود.">
      <div className="space-y-4"><div className="rounded-xl bg-[#f7f0e8] p-3"><label className="block text-sm font-bold">جست‌وجوی مشتری<input autoFocus className="btn mt-1 w-full" placeholder="نام یا شماره همراه مشتری را وارد کنید" value={customerQuery} onChange={event=>setCustomerQuery(event.target.value)}/></label>{customerQuery.trim()&&<div className="mt-3"><div className="mb-2 text-xs font-bold text-[#8d8178]">نتیجهٔ جست‌وجو</div>{matchingCustomers.length?<div className="flex flex-wrap gap-2">{matchingCustomers.map(customer=><button key={customer.id} type="button" className="btn text-xs" onClick={()=>{setCustomerName(customer.name||"");setCustomerPhone(customer.phone||"");setCustomerQuery(`${customer.name||""} ${customer.phone||""}`.trim())}}>{customer.name||"مشتری"} · {customer.phone||"بدون شماره"}</button>)}</div>:<p className="text-xs text-[#8d8178]">مشتری ثبت‌شده‌ای با این نام یا شماره همراه پیدا نشد؛ می‌توانید اطلاعات مشتری جدید را پایین وارد کنید.</p>}</div>}</div><label className="block text-sm font-bold">نام مشتری<input className="btn mt-1 w-full" placeholder={orderType==="TAKEAWAY"&&readyNotificationMethod==="SMS"?"نام مشتری":"نام مشتری (اختیاری)"} value={customerName} onChange={e=>setCustomerName(e.target.value)}/></label><label className="block text-sm font-bold">شماره همراه<input className="btn mt-1 w-full" inputMode="tel" placeholder={orderType==="TAKEAWAY"&&readyNotificationMethod==="SMS"?"برای پیامک آماده‌شدن سفارش":"برای باشگاه مشتریان و کیف پول"} value={customerPhone} onChange={e=>setCustomerPhone(e.target.value)}/></label>{orderType==="DELIVERY"&&<label className="block text-sm font-bold">آدرس کامل ارسال<textarea className="btn mt-1 min-h-24 w-full" placeholder="نشانی، پلاک و توضیحات تحویل" value={deliveryAddress} onChange={e=>setDeliveryAddress(e.target.value)}/></label>}<div className="flex justify-end border-t border-[#eadfd3] pt-4"><button type="button" className="btn btn-primary" onClick={()=>setCustomerDialog(false)}>تأیید اطلاعات</button></div></div>
    </FormDialog>
    <FormDialog open={checkoutDialog} onClose={()=>!busy&&setCheckoutDialog(false)} closeDisabled={busy} width="sm" title="تأیید نهایی سفارش" description="مبلغ نهایی توسط سامانه محاسبه شده است."><div className="space-y-3"><div className="rounded-2xl bg-[#f7f0e8] p-4"><div className="flex justify-between text-sm"><span>جمع منو</span><b>{subtotal.toLocaleString("fa-IR")} ریال</b></div>{preview&&<><div className="mt-2 flex justify-between text-sm"><span>تخفیف</span><b>-{Number(preview.discount_total).toLocaleString("fa-IR")}</b></div><div className="mt-2 flex justify-between text-sm"><span>مالیات و سرویس</span><b>{(Number(preview.tax_total)+Number(preview.service_charge_total)).toLocaleString("fa-IR")}</b></div></>}<div className="mt-3 flex justify-between border-t border-[#eadfd3] pt-3 text-xl font-black"><span>مبلغ نهایی</span><span>{Number(preview?.grand_total||0).toLocaleString("fa-IR")} ریال</span></div></div><div className="text-sm text-[#8d8178]">{deferPayment?"سفارش برای آماده‌سازی ثبت می‌شود و پرداخت در پایان سرویس انجام خواهد شد.":mixed?`پرداخت ترکیبی با ${tenders.length.toLocaleString("fa-IR")} سهم ثبت می‌شود.`:`روش پرداخت: ${{POS:"کارت‌خوان",CASH:"نقدی",CREDIT:"اعتباری",WALLET:"کیف پول",GIFT_CARD:"کارت هدیه"}[singleMethod]||singleMethod}`}</div><footer className="flex justify-end gap-2 border-t border-[#eadfd3] pt-4"><button className="btn" disabled={busy} onClick={()=>setCheckoutDialog(false)}>بازگشت</button><button className="btn btn-primary" disabled={busy} onClick={()=>{setCheckoutDialog(false);void checkout()}}>{busy?"در حال ثبت…":deferPayment?"ثبت و ارسال به آماده‌سازی":"تأیید پرداخت و ثبت"}</button></footer></div></FormDialog>
  </div>
}

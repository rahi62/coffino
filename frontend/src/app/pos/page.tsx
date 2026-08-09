"use client";
import {useEffect,useMemo,useRef,useState} from "react";
import {api} from "@/lib/api";

type Product={id:number;name:string;price:string;category:number|null;category_name?:string};
type Category={id:number;name:string};
type Tender={method:string;amount:string;tendered_amount?:string;payer_label?:string;gift_card_code?:string};

export default function POS(){
  const [products,setProducts]=useState<Product[]>([]),[categories,setCategories]=useState<Category[]>([]),[sessions,setSessions]=useState<any[]>([]),[branches,setBranches]=useState<any[]>([]),[zones,setZones]=useState<any[]>([]);
  const [category,setCategory]=useState<number|null>(null),[cart,setCart]=useState<Record<number,number>>({});
  const [orderType,setOrderType]=useState("TAKEAWAY"),[tableSession,setTableSession]=useState(""),[deliveryZone,setDeliveryZone]=useState(""),[deliveryAddress,setDeliveryAddress]=useState("");
  const [customerName,setCustomerName]=useState(""),[customerPhone,setCustomerPhone]=useState(""),[message,setMessage]=useState(""),[busy,setBusy]=useState(false);
  const [discountCode,setDiscountCode]=useState(""),[manualPercent,setManualPercent]=useState(""),[manualAmount,setManualAmount]=useState(""),[managerPin,setManagerPin]=useState("");
  const [preview,setPreview]=useState<any>(null),[deferPayment,setDeferPayment]=useState(false),[mixed,setMixed]=useState(false),[singleMethod,setSingleMethod]=useState("POS"),[singleGiftCode,setSingleGiftCode]=useState(""),[tenders,setTenders]=useState<Tender[]>([{method:"POS",amount:"",payer_label:"نفر ۱"}]),[splitGuests,setSplitGuests]=useState("2");
  const checkoutKey=useRef("");

  function load(){Promise.all([api<Product[]>("/products/"),api<Category[]>("/categories/"),api<any[]>("/table-sessions/?is_open=true"),api<any[]>("/branches/"),api<any[]>("/delivery-zones/")]).then(([p,c,s,b,z])=>{setProducts(p);setCategories(c);setSessions(s);setBranches(b);setZones(z);if(z[0]&&!deliveryZone)setDeliveryZone(z[0].code)}).catch(()=>{})}
  useEffect(load,[]);
  const shown=category?products.filter(x=>x.category===category):products;
  const subtotal=useMemo(()=>products.reduce((sum,p)=>sum+(cart[p.id]||0)*Number(p.price),0),[cart,products]);
  const manualPreview=useMemo(()=>Math.min(subtotal,Number(manualAmount||0)||subtotal*(Number(manualPercent||0)/100)),[subtotal,manualAmount,manualPercent]);
  const tenderSum=useMemo(()=>tenders.reduce((s,x)=>s+Number(x.amount||0),0),[tenders]);

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
    if(orderType==="DINE_IN"&&!tableSession){setMessage("برای سفارش داخل سالن، میز باز را انتخاب کن");return}
    setBusy(true);setMessage("");
    try{
      const {d,token}=await calculatePreview();
      let payments:Tender[]=[];
      if(!deferPayment&&mixed){
        if(Math.round(tenderSum)!==Math.round(Number(d.grand_total)))throw new Error(`جمع روش‌های پرداخت باید دقیقاً ${Number(d.grand_total).toLocaleString("fa-IR")} ریال باشد`);
        payments=tenders.map(x=>({method:x.method,amount:String(Number(x.amount)),tendered_amount:x.method==="CASH"?String(Number(x.tendered_amount||x.amount)):String(Number(x.amount)),payer_label:x.payer_label||"",gift_card_code:x.gift_card_code||""}));
      }else if(!deferPayment){
        payments=[{method:singleMethod,amount:String(Number(d.grand_total)),tendered_amount:String(Number(d.grand_total)),payer_label:"",gift_card_code:singleMethod==="GIFT_CARD"?singleGiftCode:""}];
      }
      const br=branches[0];
      const manual=(Number(manualAmount||0)>0||Number(manualPercent||0)>0)?{amount:Number(manualAmount||0),percent:Number(manualPercent||0),reason:"تخفیف دستی صندوق"}:null;
      if(!checkoutKey.current)checkoutKey.current=(globalThis.crypto?.randomUUID?.()||`${Date.now()}-${Math.random()}`);
      const order=await api<any>("/checkout/",{method:"POST",headers:{...(token?{"X-Cafino-Override":token}:{}),"Idempotency-Key":checkoutKey.current},body:JSON.stringify({
        branch:br.id,items:itemsPayload(),order_type:orderType,payments:deferPayment?null:payments,defer_payment:deferPayment,
        table_session:orderType==="DINE_IN"?Number(tableSession):null,customer_name:customerName,customer_phone:customerPhone,
        discount_code:discountCode||null,manual_discount:manual,
        delivery:orderType==="DELIVERY"?{zone_code:deliveryZone,address:deliveryAddress,recipient_name:customerName,phone:customerPhone}:null
      })});
      setCart({});setCustomerName("");setCustomerPhone("");setDiscountCode("");setManualAmount("");setManualPercent("");setManagerPin("");setSingleGiftCode("");setPreview(null);setTenders([{method:"POS",amount:"",payer_label:"نفر ۱"}]);checkoutKey.current="";
      setMessage(`✓ سفارش ${order.order_number} ثبت شد — مبلغ نهایی ${Number(order.grand_total).toLocaleString("fa-IR")} ریال`);
    }catch(e:any){setMessage(`خطا: ${e?.message||"نامشخص"}`)}finally{setBusy(false)}
  }

  function addTender(){setTenders(x=>[...x,{method:"CASH",amount:"",payer_label:`نفر ${x.length+1}`}])}
  function equalSplit(){
    if(!preview){setMessage("ابتدا مبلغ نهایی را محاسبه کن");return}
    const count=Math.max(2,Math.min(20,Number(splitGuests||2)));const total=Math.round(Number(preview.grand_total));const base=Math.floor(total/count);const rem=total-base*count;
    setMixed(true);setTenders(Array.from({length:count},(_,i)=>({method:"POS",amount:String(base+(i===0?rem:0)),payer_label:`نفر ${i+1}`})));
  }
  return <div>
    <div className="flex flex-wrap justify-between gap-4 items-end mb-5">
      <div><h1 className="text-3xl font-black">فروش جدید</h1><p className="text-[#8d8178]">Preview قطعی Backend ← مالیات/سرویس ← Mixed Payment ← آماده‌سازی</p></div>
      <div className="flex flex-wrap gap-2"><select className="btn" value={orderType} onChange={e=>{setOrderType(e.target.value);invalidate()}}><option value="TAKEAWAY">بیرون‌بر</option><option value="DINE_IN">داخل سالن</option><option value="PICKUP">تحویل حضوری</option><option value="DELIVERY">ارسال</option></select>
      {orderType==="DINE_IN"&&<select className="btn" value={tableSession} onChange={e=>setTableSession(e.target.value)}><option value="">میز باز...</option>{sessions.map(s=><option key={s.id} value={s.id}>میز {s.table_number}</option>)}</select>}{orderType==="DELIVERY"&&<select className="btn" value={deliveryZone} onChange={e=>{setDeliveryZone(e.target.value);invalidate()}}><option value="">منطقه ارسال...</option>{zones.map(z=><option key={z.id} value={z.code}>{z.name}</option>)}</select>}</div>
    </div>
    {message&&<div className="card p-3 mb-4">{message}</div>}
    <div className="grid grid-cols-[140px_minmax(0,1fr)_420px] gap-4">
      <div className="card p-3 space-y-2"><button className="btn w-full" onClick={()=>setCategory(null)}>همه</button>{categories.map(c=><button className="btn w-full" key={c.id} onClick={()=>setCategory(c.id)}>{c.name}</button>)}</div>
      <div className="grid grid-cols-2 xl:grid-cols-3 gap-3 content-start">{shown.map(p=><button key={p.id} className="card p-4 text-right hover:-translate-y-1 transition" onClick={()=>inc(p.id)}><div className="font-bold text-lg">{p.name}</div><div className="text-xs text-[#8d8178] mt-1">{p.category_name||"بدون دسته"}</div><div className="text-[#b9792d] mt-4 font-bold">{Number(p.price).toLocaleString("fa-IR")} ریال</div></button>)}</div>
      <div className="card p-4">
        <h2 className="font-black text-xl mb-3">سفارش جاری</h2>
        <div className="grid grid-cols-2 gap-2 mb-3"><input className="border rounded-xl p-2" placeholder="نام مشتری (اختیاری)" value={customerName} onChange={e=>setCustomerName(e.target.value)}/><input className="border rounded-xl p-2" placeholder="موبایل برای Loyalty/Wallet/SMS" value={customerPhone} onChange={e=>setCustomerPhone(e.target.value)}/></div>{orderType==="DELIVERY"&&<textarea className="border rounded-xl p-2 w-full mb-3" placeholder="آدرس کامل ارسال" value={deliveryAddress} onChange={e=>setDeliveryAddress(e.target.value)}/>}
        <div className="space-y-2 min-h-44 max-h-[28vh] overflow-auto">{products.filter(p=>cart[p.id]).map(p=><div key={p.id} className="flex justify-between items-center border-b pb-2"><div><b>{p.name}</b><div className="text-xs text-[#8d8178]">{(Number(p.price)*(cart[p.id]||0)).toLocaleString("fa-IR")}</div></div><div className="flex items-center gap-2"><button className="btn" onClick={()=>dec(p.id)}>−</button><b>{cart[p.id]}</b><button className="btn" onClick={()=>inc(p.id)}>+</button></div></div>)}</div>
        <div className="border-t pt-3 mt-3 space-y-2"><input className="border rounded-xl p-2 w-full" placeholder="کد تخفیف" value={discountCode} onChange={e=>{setDiscountCode(e.target.value);invalidate()}}/><div className="grid grid-cols-2 gap-2"><input className="border rounded-xl p-2" placeholder="تخفیف %" value={manualPercent} onChange={e=>{setManualPercent(e.target.value);invalidate()}}/><input className="border rounded-xl p-2" placeholder="تخفیف مبلغ" value={manualAmount} onChange={e=>{setManualAmount(e.target.value);invalidate()}}/></div>{(manualPreview>0||discountCode)&&<input type="password" inputMode="numeric" className="border rounded-xl p-2 w-full" placeholder="PIN مدیر در صورت نیاز" value={managerPin} onChange={e=>setManagerPin(e.target.value)}/>}</div>
        <button className="btn w-full mt-3" onClick={()=>calculatePreview().catch(e=>setMessage(e.message))}>محاسبه مبلغ نهایی</button>
        <div className="mt-3 text-sm space-y-1"><div className="flex justify-between"><span>جمع منو</span><b>{subtotal.toLocaleString("fa-IR")}</b></div>{preview&&<><div className="flex justify-between"><span>تخفیف</span><b>-{Number(preview.discount_total).toLocaleString("fa-IR")}</b></div><div className="flex justify-between"><span>حق سرویس</span><b>{Number(preview.service_charge_total).toLocaleString("fa-IR")}</b></div><div className="flex justify-between"><span>مالیات</span><b>{Number(preview.tax_total).toLocaleString("fa-IR")}</b></div><div className="flex justify-between text-xl font-black"><span>نهایی</span><span>{Number(preview.grand_total).toLocaleString("fa-IR")} ریال</span></div></>}</div>
        <div className="border-t mt-3 pt-3">{orderType==="DINE_IN"&&<label className="flex gap-2 items-center mb-2"><input type="checkbox" checked={deferPayment} onChange={e=>setDeferPayment(e.target.checked)}/> ارسال به آماده‌سازی و پرداخت در پایان سرویس</label>}<label className={`flex gap-2 items-center mb-2 ${deferPayment?"opacity-40":""}`}><input disabled={deferPayment} type="checkbox" checked={mixed} onChange={e=>setMixed(e.target.checked)}/> تقسیم / Mixed Payment</label>
        {deferPayment?<div className="bg-[#eee6dc] rounded-xl p-3 text-sm">سفارش بدون Payment ثبت می‌شود و بعداً از Split Bill یا تسویه سفارش پرداخت خواهد شد.</div>:!mixed?<div className="space-y-2"><select className="btn w-full" value={singleMethod} onChange={e=>setSingleMethod(e.target.value)}><option value="POS">کارتخوان</option><option value="CASH">نقدی</option><option value="CREDIT">اعتباری</option><option value="WALLET">کیف پول</option><option value="GIFT_CARD">کارت هدیه</option></select>{singleMethod==="GIFT_CARD"&&<input className="border rounded-xl p-2 w-full" placeholder="کد کارت هدیه" value={singleGiftCode} onChange={e=>setSingleGiftCode(e.target.value)}/>}</div>:<div className="space-y-2">
          <div className="flex gap-2"><input className="border rounded-xl p-2 w-24" value={splitGuests} onChange={e=>setSplitGuests(e.target.value)} placeholder="نفر"/><button className="btn" onClick={equalSplit}>تقسیم مساوی</button></div>
          {tenders.map((t,i)=><div className="grid grid-cols-[100px_120px_1fr_42px] gap-2" key={i}><input className="border rounded-xl p-2" placeholder="پرداخت‌کننده" value={t.payer_label||""} onChange={e=>setTenders(x=>x.map((z,j)=>j===i?{...z,payer_label:e.target.value}:z))}/><select className="btn" value={t.method} onChange={e=>setTenders(x=>x.map((z,j)=>j===i?{...z,method:e.target.value}:z))}><option value="POS">کارتخوان</option><option value="CASH">نقدی</option><option value="CREDIT">اعتباری</option><option value="WALLET">کیف پول</option><option value="GIFT_CARD">کارت هدیه</option></select><input className="border rounded-xl p-2" placeholder={t.method==="GIFT_CARD"?"مبلغ؛ کد را پایین وارد کن":"مبلغ"} value={t.amount} onChange={e=>setTenders(x=>x.map((z,j)=>j===i?{...z,amount:e.target.value}:z))}/><button className="btn" onClick={()=>setTenders(x=>x.filter((_,j)=>j!==i))}>×</button>{t.method==="GIFT_CARD"&&<input className="border rounded-xl p-2 col-span-4" placeholder="کد کارت هدیه" value={t.gift_card_code||""} onChange={e=>setTenders(x=>x.map((z,j)=>j===i?{...z,gift_card_code:e.target.value}:z))}/>}</div>)}
          <button className="btn" onClick={addTender}>+ روش پرداخت</button><div className="text-sm">جمع Paymentها: <b>{tenderSum.toLocaleString("fa-IR")}</b></div></div>}</div>
        <button disabled={busy} onClick={checkout} className="btn btn-primary w-full text-lg mt-4 disabled:opacity-50">{busy?"در حال ثبت...":"پرداخت و ارسال به آماده‌سازی"}</button>
      </div>
    </div>
  </div>
}

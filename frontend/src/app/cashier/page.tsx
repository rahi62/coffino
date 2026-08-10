"use client";

import {useEffect, useMemo, useState} from "react";
import FormDialog from "@/components/form-dialog";
import {api} from "@/lib/api";
import {label} from "@/lib/i18n";

type Branch = {id:number; name:string; is_active:boolean};
type CashRegister = {id:number; branch:number; name:string; is_active:boolean};
type CashShift = {
  id:number; register:number; opening_balance:string; expected_cash:string;
  difference:string; is_open:boolean;
};
type CashMovement = {id:number; movement_type:string; amount:string; note:string};

const normalizeDigits=(value:string)=>value
  .replace(/[۰-۹]/g, digit=>String("۰۱۲۳۴۵۶۷۸۹".indexOf(digit)))
  .replace(/[٠-٩]/g, digit=>String("٠١٢٣٤٥٦٧٨٩".indexOf(digit)))
  .replace(/[٬,\s]/g, "");

const money=(value:string|number)=>Number(value||0).toLocaleString("fa-IR");

export default function Cashier(){
  const [branches,setBranches]=useState<Branch[]>([]);
  const [registers,setRegisters]=useState<CashRegister[]>([]);
  const [shifts,setShifts]=useState<CashShift[]>([]);
  const [movements,setMovements]=useState<CashMovement[]>([]);
  const [selectedBranchId,setSelectedBranchId]=useState<number|"">("");
  const [selectedRegisterId,setSelectedRegisterId]=useState<number|"">("");
  const [registerName,setRegisterName]=useState("");
  const [opening,setOpening]=useState("");
  const [msg,setMsg]=useState("");
  const [loading,setLoading]=useState(true);
  const [creatingRegister,setCreatingRegister]=useState(false);
  const [openingShift,setOpeningShift]=useState(false);
  const [dialog,setDialog]=useState<"register"|"open"|"close"|null>(null);
  const [closingShift,setClosingShift]=useState<CashShift|null>(null);
  const [actualCash,setActualCash]=useState("0");

  const load=async()=>{
    setLoading(true);
    try{
      const [branchData,registerData,shiftData,movementData]=await Promise.all([
        api<Branch[]>("/branches/"), api<CashRegister[]>("/cash-registers/"),
        api<CashShift[]>("/cash-shifts/"), api<CashMovement[]>("/cash-movements/"),
      ]);
      setBranches(branchData.filter(branch=>branch.is_active));
      setRegisters(registerData);
      setShifts(shiftData);
      setMovements(movementData);
      setSelectedBranchId(current=>{
        const stored=Number(localStorage.getItem("cafino_settings_branch")||0);
        if(branchData.some(branch=>branch.id===current&&branch.is_active)) return current;
        if(branchData.some(branch=>branch.id===stored&&branch.is_active)) return stored;
        return branchData.find(branch=>branch.is_active)?.id||"";
      });
    }catch(error:any){
      setMsg(error.message||"دریافت اطلاعات صندوق انجام نشد.");
    }finally{setLoading(false)}
  };

  useEffect(()=>{void load()},[]);

  const branchRegisters=useMemo(
    ()=>registers.filter(register=>register.branch===selectedBranchId&&register.is_active),
    [registers,selectedBranchId],
  );
  const selectedBranch=branches.find(branch=>branch.id===selectedBranchId);
  const selectedRegister=branchRegisters.find(register=>register.id===selectedRegisterId);
  const activeShift=shifts.find(shift=>shift.register===selectedRegister?.id&&shift.is_open);
  const branchRegisterIds=new Set(branchRegisters.map(register=>register.id));
  const branchShifts=shifts.filter(shift=>branchRegisterIds.has(shift.register));

  useEffect(()=>{
    setSelectedRegisterId(current=>branchRegisters.some(register=>register.id===current)
      ? current
      : branchRegisters[0]?.id||"");
  },[selectedBranchId, registers]);

  function changeBranch(id:number){
    setSelectedBranchId(id);
    localStorage.setItem("cafino_settings_branch",String(id));
    setMsg("");
  }

  async function createRegister(){
    if(!selectedBranch){setMsg("ابتدا شعبهٔ فعال را انتخاب کنید.");return}
    if(!registerName.trim()){setMsg("نام صندوق را وارد کنید.");return}
    setCreatingRegister(true);setMsg("");
    try{
      const created=await api<CashRegister>("/cash-registers/",{
        method:"POST",
        body:JSON.stringify({branch:selectedBranch.id,name:registerName.trim(),is_active:true}),
      });
      setRegisters(current=>[...current,created]);
      setSelectedRegisterId(created.id);
      setRegisterName("");
      setDialog(null);
      setMsg("صندوق ایجاد شد. اکنون موجودی افتتاحیه را وارد و شیفت را باز کنید.");
    }catch(error:any){
      setMsg(error.message||"ایجاد صندوق انجام نشد.");
    }finally{setCreatingRegister(false)}
  }

  async function openShift(){
    if(!selectedRegister){setMsg("ابتدا یک صندوق فعال برای این شعبه ایجاد یا انتخاب کنید.");return}
    const openingBalance=normalizeDigits(opening);
    if(!/^\d+$/.test(openingBalance)){
      setMsg("موجودی افتتاحیه را به ریال و به‌صورت صفر یا عدد مثبت وارد کنید.");
      return;
    }
    setOpeningShift(true);setMsg("");
    try{
      await api("/cash-shifts/",{
        method:"POST",
        body:JSON.stringify({register:selectedRegister.id,opening_balance:openingBalance,is_open:true}),
      });
      setOpening("");
      setDialog(null);
      setMsg("شیفت صندوق باز شد.");
      await load();
    }catch(error:any){
      setMsg(error.message||"بازکردن شیفت انجام نشد.");
    }finally{setOpeningShift(false)}
  }

  async function closeShift(){
    if(!closingShift)return;
    const normalizedActualCash=normalizeDigits(actualCash);
    if(!/^\d+$/.test(normalizedActualCash)){setMsg("موجودی واقعی را به‌صورت صفر یا عدد مثبت وارد کنید.");return}
    try{
      await api(`/cash-shifts/${closingShift.id}/close/`,{method:"POST",body:JSON.stringify({actual_cash:normalizedActualCash})});
      setMsg("شیفت صندوق بسته شد.");
      setDialog(null);setClosingShift(null);
      await load();
    }catch(error:any){setMsg(error.message||"بستن شیفت انجام نشد.")}
  }

  return <div>
    <div className="mb-5 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
      <div><h1 className="text-3xl font-black">صندوق و دفتر گردش نقدی</h1><p className="mt-1 text-sm text-[#8d8178]">شیفت نقدی هر شعبه و صندوق را جداگانه مدیریت کنید.</p></div>
      <label className="text-sm font-bold">شعبهٔ فعال
        <select className="btn mt-1 block min-w-56" value={selectedBranchId} onChange={event=>changeBranch(Number(event.target.value))} disabled={loading||!branches.length}>
          {!branches.length&&<option value="">شعبه‌ای در دسترس نیست</option>}
          {branches.map(branch=><option key={branch.id} value={branch.id}>{branch.name}</option>)}
        </select>
      </label>
    </div>

    <div className="grid gap-4 lg:grid-cols-3">
      <section className="card p-5">
        <h2 className="mb-1 font-black">شروع شیفت</h2>
        <p className="mb-4 text-sm text-[#8d8178]">مبلغ نقدی موجود در کشوی صندوق در ابتدای شیفت را ثبت کنید.</p>

        {selectedBranch&&!branchRegisters.length&&<div className="mb-4 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-950">
          <b>برای شعبهٔ «{selectedBranch.name}» هنوز صندوقی تعریف نشده است.</b>
          <p className="mt-1 leading-5">برای شروع شیفت و ثبت تسویهٔ نقدی، ابتدا یک صندوق ایجاد کنید.</p>
          <button className="btn btn-primary mt-3 w-full disabled:cursor-not-allowed disabled:opacity-50" onClick={()=>setDialog("register")} disabled={creatingRegister}>ایجاد صندوق</button>
        </div>}

        {!!branchRegisters.length&&<label className="mb-3 block text-sm font-bold" htmlFor="cash-register">صندوق فعال
          <select id="cash-register" className="btn mt-1 w-full" value={selectedRegisterId} onChange={event=>setSelectedRegisterId(Number(event.target.value))}>
            {branchRegisters.map(register=><option key={register.id} value={register.id}>{register.name}</option>)}
          </select>
        </label>}

        <label className="block text-sm font-bold" htmlFor="opening-balance">موجودی افتتاحیه (ریال)</label>
        <input id="opening-balance" className="btn mt-1 w-full" inputMode="numeric" placeholder="مثلاً ۵۰۰٬۰۰۰" value={opening} onChange={event=>setOpening(event.target.value)} disabled={!selectedRegister||Boolean(activeShift)} />
        <p className="mt-2 text-xs leading-5 text-[#8d8178]">اگر وجه نقدی در صندوق نیست، عدد «۰» را وارد کنید. این مبلغ مبنای محاسبهٔ اختلاف پایان شیفت است.</p>

        {activeShift&&<div className="mt-3 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900"><b>یک شیفت برای این صندوق باز است.</b><p className="mt-1">برای شروع شیفت جدید، ابتدا همان شیفت را از فهرست روبه‌رو ببندید.</p></div>}
        <button className="btn btn-primary mt-4 w-full disabled:cursor-not-allowed disabled:opacity-50" onClick={()=>setDialog("open")} disabled={openingShift||!selectedRegister||Boolean(activeShift)}>
          {openingShift?"در حال بازکردن شیفت…":activeShift?"ابتدا شیفت فعال را ببندید":!selectedRegister?"ابتدا صندوق را انتخاب کنید":"باز کردن شیفت"}
        </button>
        {msg&&<p role="status" className="mt-3 text-sm leading-6">{msg}</p>}
        <p className="mt-4 text-xs leading-5 text-[#8d8178]">فقط فروش، هزینه و برگشت وجه نقدی وارد کشوی صندوق می‌شوند. تراکنش کارت‌خوان در دفتر گردش نقدی ثبت نمی‌شود.</p>
      </section>

      <section className="space-y-3 lg:col-span-2">
        {loading?<div className="card p-5 text-sm text-[#8d8178]">در حال دریافت اطلاعات صندوق…</div>:branchShifts.length?branchShifts.map(shift=><div className="card flex items-center justify-between gap-3 p-4" key={shift.id}><div><b>شیفت #{shift.id}</b><div className="mt-1 text-sm text-[#8d8178]">افتتاحیه {money(shift.opening_balance)} | مورد انتظار {money(shift.expected_cash)}</div></div>{shift.is_open?<button className="btn" onClick={()=>{setClosingShift(shift);setActualCash("0");setDialog("close")}}>بستن شیفت</button>:<span className="badge">اختلاف {money(shift.difference)}</span>}</div>):<div className="card p-5 text-sm text-[#8d8178]">هنوز شیفتی برای صندوق‌های این شعبه ثبت نشده است.</div>}
      </section>
    </div>

    <h2 className="mb-3 mt-7 text-xl font-black">آخرین حرکات نقدی</h2>
    <div className="card overflow-x-auto"><table className="w-full min-w-[500px]"><thead className="bg-[#eee6dc]"><tr><th className="p-3 text-right">نوع</th><th className="text-right">مبلغ</th><th className="text-right">توضیح</th></tr></thead><tbody>{movements.slice(0,30).map(movement=><tr className="border-t" key={movement.id}><td className="p-3">{label(movement.movement_type)}</td><td>{money(movement.amount)}</td><td>{movement.note||"—"}</td></tr>)}{!movements.length&&<tr><td colSpan={3} className="p-5 text-center text-sm text-[#8d8178]">هنوز گردش نقدی ثبت نشده است.</td></tr>}</tbody></table></div>
    <FormDialog open={dialog==="register"} onClose={()=>setDialog(null)} closeDisabled={creatingRegister} width="sm" title="ایجاد صندوق" description={selectedBranch?`این صندوق برای شعبهٔ «${selectedBranch.name}» ایجاد می‌شود.`:undefined}><label className="block text-sm font-bold">نام صندوق<input autoFocus className="btn mt-1 w-full" placeholder="مثلاً صندوق اصلی" value={registerName} onChange={event=>setRegisterName(event.target.value)}/></label><footer className="mt-5 flex justify-end gap-2"><button className="btn" disabled={creatingRegister} onClick={()=>setDialog(null)}>انصراف</button><button className="btn btn-primary" disabled={creatingRegister||!registerName.trim()} onClick={()=>void createRegister()}>{creatingRegister?"در حال ایجاد…":"ثبت صندوق"}</button></footer></FormDialog>
    <FormDialog open={dialog==="open"} onClose={()=>setDialog(null)} closeDisabled={openingShift} width="sm" title="تأیید شروع شیفت" description={selectedRegister?`شیفت جدید برای صندوق «${selectedRegister.name}» باز می‌شود.`:undefined}><div className="rounded-xl bg-[#f7f0e8] p-3 text-sm">موجودی افتتاحیه: <b>{money(normalizeDigits(opening)||0)} ریال</b></div><p className="mt-3 text-sm text-[#8d8178]">بعد از ثبت، این مبلغ مبنای محاسبهٔ اختلاف پایان شیفت است.</p><footer className="mt-5 flex justify-end gap-2"><button className="btn" disabled={openingShift} onClick={()=>setDialog(null)}>بازگشت</button><button className="btn btn-primary" disabled={openingShift} onClick={()=>void openShift()}>{openingShift?"در حال بازکردن…":"تأیید و باز کردن شیفت"}</button></footer></FormDialog>
    <FormDialog open={dialog==="close"} onClose={()=>{setDialog(null);setClosingShift(null)}} width="sm" title="بستن شیفت صندوق" description={closingShift?`مبلغ مورد انتظار: ${money(closingShift.expected_cash)} ریال`:undefined}><label className="block text-sm font-bold">موجودی واقعی نقدی (ریال)<input autoFocus className="btn mt-1 w-full" inputMode="numeric" placeholder="مثلاً ۵۰۰٬۰۰۰ یا ۰" value={actualCash} onChange={event=>setActualCash(event.target.value)}/></label><p className="mt-3 rounded-xl bg-amber-50 p-3 text-sm text-amber-900">پس از تأیید، اختلاف نقدی ثبت و شیفت بسته می‌شود. این عملیات را فقط پس از شمارش واقعی وجه نقد انجام دهید.</p><footer className="mt-5 flex justify-end gap-2"><button className="btn" onClick={()=>{setDialog(null);setClosingShift(null)}}>بازگشت</button><button className="btn btn-primary" onClick={()=>void closeShift()}>تأیید و بستن شیفت</button></footer></FormDialog>
  </div>;
}

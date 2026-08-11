"use client";

import {useEffect, useMemo, useState} from "react";
import FormDialog from "@/components/form-dialog";
import {LocalizedDateInput} from "@/components/localized-date-input";
import {api} from "@/lib/api";

type PurchaseRow = {inventory_item:string; quantity:string; unit_cost:string; lot_number:string; expires_at:string};
type Branch = {id:number; name:string; is_active:boolean};
type Supplier = {id:number; branch:number; name:string};
type InventoryItem = {id:number; branch:number; name:string; lot_tracked:boolean};
type BankAccount = {id:number; branch:number; display_name:string; is_active:boolean};
type PurchaseInvoice = {id:number; branch:number; supplier_name:string; total_amount:string; paid_amount:string; balance_due:string};
type PaymentMethod = "CASH" | "POS";
type Dialog = "purchase" | "payment" | null;

const emptyRow = (): PurchaseRow => ({inventory_item:"", quantity:"1", unit_cost:"0", lot_number:"", expires_at:""});
const money = (value:string|number) => Number(value || 0).toLocaleString("fa-IR");

export default function Purchasing(){
  const [suppliers,setSuppliers] = useState<Supplier[]>([]);
  const [inventory,setInventory] = useState<InventoryItem[]>([]);
  const [invoices,setInvoices] = useState<PurchaseInvoice[]>([]);
  const [branches,setBranches] = useState<Branch[]>([]);
  const [accounts,setAccounts] = useState<BankAccount[]>([]);
  const [selectedBranchId,setSelectedBranchId] = useState<number|"">("");
  const [supplier,setSupplier] = useState("");
  const [paid,setPaid] = useState("0");
  const [method,setMethod] = useState<PaymentMethod>("CASH");
  const [bankAccount,setBankAccount] = useState("");
  const [rows,setRows] = useState<PurchaseRow[]>([emptyRow()]);
  const [paymentInvoice,setPaymentInvoice] = useState<PurchaseInvoice|null>(null);
  const [paymentForm,setPaymentForm] = useState({amount:"", method:"CASH" as PaymentMethod, bank_account:"", reference:""});
  const [dialog,setDialog] = useState<Dialog>(null);
  const [busy,setBusy] = useState(false);
  const [message,setMessage] = useState("");
  const [formError,setFormError] = useState("");

  const load = async () => {
    const [nextSuppliers,nextInventory,nextInvoices,nextBranches,nextAccounts] = await Promise.all([
      api<Supplier[]>("/suppliers/"), api<InventoryItem[]>("/inventory-items/"), api<PurchaseInvoice[]>("/purchase-invoices/"),
      api<Branch[]>("/branches/"), api<BankAccount[]>("/bank-accounts/"),
    ]);
    setSuppliers(nextSuppliers);
    setInventory(nextInventory);
    setInvoices(nextInvoices);
    setBranches(nextBranches.filter(branch => branch.is_active));
    setAccounts(nextAccounts);
    setSelectedBranchId(current => {
      const stored = Number(localStorage.getItem("cafino_settings_branch") || 0);
      if (nextBranches.some(branch => branch.id === current && branch.is_active)) return current;
      if (nextBranches.some(branch => branch.id === stored && branch.is_active)) return stored;
      return nextBranches.find(branch => branch.is_active)?.id || "";
    });
  };

  useEffect(() => { void load().catch(error => setMessage(error.message || "دریافت اطلاعات خرید انجام نشد.")); }, []);

  const branchSuppliers = useMemo(() => suppliers.filter(item => item.branch === selectedBranchId), [suppliers,selectedBranchId]);
  const branchInventory = useMemo(() => inventory.filter(item => item.branch === selectedBranchId), [inventory,selectedBranchId]);
  const branchAccounts = useMemo(() => accounts.filter(item => item.branch === selectedBranchId && item.is_active), [accounts,selectedBranchId]);
  const branchInvoices = useMemo(() => invoices.filter(item => item.branch === selectedBranchId), [invoices,selectedBranchId]);
  const total = useMemo(() => rows.reduce((sum,row) => sum + Number(row.quantity || 0) * Number(row.unit_cost || 0), 0), [rows]);

  const closeDialog = () => {
    if (!busy) { setDialog(null); setFormError(""); setPaymentInvoice(null); }
  };
  const resetPurchase = () => {
    setSupplier(""); setPaid("0"); setMethod("CASH"); setBankAccount(""); setRows([emptyRow()]); setFormError("");
  };
  const openPurchase = () => { resetPurchase(); setDialog("purchase"); };
  const changeBranch = (branchId:number) => {
    setSelectedBranchId(branchId);
    localStorage.setItem("cafino_settings_branch", String(branchId));
    setMessage("");
  };
  const setRow = (index:number, key:keyof PurchaseRow, value:string) => setRows(current => current.map((row,rowIndex) => rowIndex === index ? {...row,[key]:value} : row));
  const addRow = () => setRows(current => [...current,emptyRow()]);
  const removeRow = (index:number) => setRows(current => current.length === 1 ? [emptyRow()] : current.filter((_,rowIndex) => rowIndex !== index));

  const validateBankAccount = (paymentMethod:PaymentMethod, selectedAccount:string) => {
    if (paymentMethod === "POS" && !selectedAccount) {
      setFormError("برای پرداخت با کارت یا حساب بانکی، مقصد پرداخت را انتخاب کنید.");
      return false;
    }
    return true;
  };

  const createPurchase = async () => {
    const items = rows.filter(row => row.inventory_item);
    if (!selectedBranchId) { setFormError("ابتدا شعبهٔ فعال را انتخاب کنید."); return; }
    if (!supplier) { setFormError("تأمین‌کننده را انتخاب کنید."); return; }
    if (!items.length) { setFormError("حداقل یک مادهٔ اولیه به فاکتور اضافه کنید."); return; }
    if (!items.every(row => Number(row.quantity) > 0 && Number(row.unit_cost) >= 0)) { setFormError("تعداد و بهای واحد هر ردیف را به‌درستی وارد کنید."); return; }
    if (Number(paid) < 0 || !validateBankAccount(method, bankAccount)) return;
    setBusy(true); setFormError("");
    try {
      await api("/purchases/create/", {
        method:"POST",
        body:JSON.stringify({
          branch:selectedBranchId, supplier:Number(supplier), invoice_date:new Date().toISOString().slice(0,10),
          items:items.map(row => ({...row,inventory_item:Number(row.inventory_item),expires_at:row.expires_at || null})),
          paid_amount:paid, payment_method:method, bank_account:method === "POS" ? Number(bankAccount) : null,
        }),
      });
      resetPurchase(); setDialog(null);
      setMessage("فاکتور خرید با موفقیت ثبت شد و موجودی انبار به‌روزرسانی شد.");
      await load();
    } catch (error:any) { setFormError(error.message || "ثبت فاکتور خرید انجام نشد."); }
    finally { setBusy(false); }
  };

  const openPayment = (invoice:PurchaseInvoice) => {
    setPaymentInvoice(invoice);
    setPaymentForm({amount:String(invoice.balance_due),method:"CASH",bank_account:"",reference:""});
    setFormError(""); setDialog("payment");
  };
  const submitPayment = async () => {
    if (!paymentInvoice) return;
    if (Number(paymentForm.amount) <= 0 || Number(paymentForm.amount) > Number(paymentInvoice.balance_due)) {
      setFormError("مبلغ پرداخت باید بیشتر از صفر و حداکثر برابر ماندهٔ فاکتور باشد."); return;
    }
    if (!validateBankAccount(paymentForm.method,paymentForm.bank_account)) return;
    setBusy(true); setFormError("");
    try {
      await api(`/purchase-invoices/${paymentInvoice.id}/pay/`, {
        method:"POST",
        body:JSON.stringify({
          amount:paymentForm.amount, method:paymentForm.method, reference:paymentForm.reference.trim(),
          bank_account:paymentForm.method === "POS" ? Number(paymentForm.bank_account) : null,
        }),
      });
      setDialog(null); setPaymentInvoice(null);
      setMessage("پرداخت تأمین‌کننده با موفقیت ثبت شد.");
      await load();
    } catch (error:any) { setFormError(error.message || "ثبت پرداخت انجام نشد."); }
    finally { setBusy(false); }
  };

  return <div className="space-y-5">
    <header className="flex flex-col gap-3 rounded-[22px] border border-[#eadfd3] bg-[#fffdf9] p-5 shadow-sm sm:flex-row sm:items-end sm:justify-between">
      <div><p className="mb-1 text-sm font-bold text-[#b9792d]">خرید و تأمین</p><h1 className="text-3xl font-black">فاکتورهای خرید</h1><p className="mt-2 text-[#8d8178]">خرید مواد اولیه، ورود موجودی و پرداخت تأمین‌کنندگان را از یک مسیر مدیریت کنید.</p></div>
      <button className="btn btn-primary self-start" onClick={openPurchase} disabled={!selectedBranchId}>ثبت فاکتور خرید</button>
    </header>

    {message && <div role="status" className="card border-r-4 border-r-emerald-600 p-4 text-emerald-950">{message}</div>}

    <section className="card flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
      <label className="text-sm font-bold">شعبهٔ فعال
        <select className="btn mr-2 mt-1 min-w-52 sm:mt-0" value={selectedBranchId} onChange={event => changeBranch(Number(event.target.value))}>
          {!branches.length && <option value="">شعبه‌ای در دسترس نیست</option>}
          {branches.map(branch => <option key={branch.id} value={branch.id}>{branch.name}</option>)}
        </select>
      </label>
      <p className="text-sm text-[#8d8178]">پرداخت نقدی در گردش صندوق و پرداخت کارت یا بانک در حساب انتخاب‌شده ثبت می‌شود.</p>
    </section>

    <section className="space-y-3">
      <div><h2 className="text-xl font-black">فاکتورهای ثبت‌شده</h2><p className="mt-1 text-sm text-[#8d8178]">برای مانده‌دارها می‌توانید پرداخت بعدی را ثبت کنید.</p></div>
      {branchInvoices.length ? branchInvoices.map(invoice => <article className="card flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between" key={invoice.id}>
        <div><b>{invoice.supplier_name}</b><div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-sm text-[#8d8178]"><span>کل {money(invoice.total_amount)} ریال</span><span>پرداخت {money(invoice.paid_amount)} ریال</span><span>مانده {money(invoice.balance_due)} ریال</span></div></div>
        {Number(invoice.balance_due) > 0 && <button className="btn self-start sm:self-auto" onClick={() => openPayment(invoice)}>ثبت پرداخت</button>}
      </article>) : <div className="card p-10 text-center text-[#8d8178]">برای شعبهٔ انتخاب‌شده فاکتور خریدی ثبت نشده است.</div>}
    </section>

    <FormDialog open={dialog === "purchase"} onClose={closeDialog} closeDisabled={busy} width="lg" title="ثبت فاکتور خرید" description="پس از ثبت، موجودی مواد اولیه به‌روزرسانی می‌شود؛ اطلاعات را پیش از تأیید بررسی کنید.">
      <div className="space-y-4">
        {formError && <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-900">{formError}</div>}
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <label className="text-sm font-bold">تأمین‌کننده<select autoFocus className="btn mt-1 w-full" value={supplier} onChange={event => setSupplier(event.target.value)}><option value="">انتخاب تأمین‌کننده</option>{branchSuppliers.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
          <label className="text-sm font-bold">پرداخت اولیه (ریال)<input className="btn mt-1 w-full" inputMode="numeric" placeholder="مثلاً ۵۰۰٬۰۰۰" value={paid} onChange={event => setPaid(event.target.value)}/></label>
          <label className="text-sm font-bold">روش پرداخت<select className="btn mt-1 w-full" value={method} onChange={event => { setMethod(event.target.value as PaymentMethod); setBankAccount(""); }}><option value="CASH">نقدی</option><option value="POS">کارت یا حساب بانکی</option></select></label>
          {method === "POS" && <label className="text-sm font-bold sm:col-span-2 lg:col-span-3">کارت یا حساب پرداخت‌کننده<select className="btn mt-1 w-full" value={bankAccount} onChange={event => setBankAccount(event.target.value)}><option value="">انتخاب کارت یا حساب</option>{branchAccounts.map(account => <option key={account.id} value={account.id}>{account.display_name}</option>)}</select>{!branchAccounts.length && <span className="mt-1 block text-xs text-amber-800">کارت یا حساب فعالی برای این شعبه ثبت نشده است. ابتدا از بخش «کارت‌ها و حساب‌های بانکی» آن را تعریف کنید.</span>}</label>}
        </div>
        <div className="overflow-x-auto rounded-xl border border-[#eadfd3]"><div className="min-w-[860px] space-y-2 p-3">
          <div className="grid grid-cols-[minmax(190px,1fr)_100px_130px_150px_190px_42px] gap-2 px-1 text-xs font-bold text-[#8d8178]"><span>مادهٔ اولیه</span><span>تعداد</span><span>بهای واحد</span><span>شماره سری ساخت</span><span>تاریخ انقضا</span><span aria-label="حذف ردیف" /></div>
          {rows.map((row,index) => <div className="grid grid-cols-[minmax(190px,1fr)_100px_130px_150px_190px_42px] gap-2" key={index}>
            <select className="btn" value={row.inventory_item} onChange={event => setRow(index,"inventory_item",event.target.value)}><option value="">انتخاب مادهٔ اولیه</option>{branchInventory.map(item => <option value={item.id} key={item.id}>{item.name}{item.lot_tracked ? " · سری ساخت" : ""}</option>)}</select>
            <input className="btn" inputMode="decimal" placeholder="تعداد" value={row.quantity} onChange={event => setRow(index,"quantity",event.target.value)}/>
            <input className="btn" inputMode="numeric" placeholder="بهای واحد" value={row.unit_cost} onChange={event => setRow(index,"unit_cost",event.target.value)}/>
            <input className="btn" placeholder="اختیاری" value={row.lot_number} onChange={event => setRow(index,"lot_number",event.target.value)}/>
            <LocalizedDateInput withTime value={row.expires_at} onChange={expiresAt => setRow(index,"expires_at",expiresAt)}/>
            <button type="button" className="btn px-2" aria-label="حذف ردیف" onClick={() => removeRow(index)}>×</button>
          </div>)}
        </div></div>
        <div className="flex flex-col gap-3 border-t border-[#eadfd3] pt-4 sm:flex-row sm:items-center sm:justify-between"><button type="button" className="btn self-start" onClick={addRow}>افزودن ردیف</button><b>جمع فاکتور: {money(total)} ریال</b></div>
        <footer className="flex flex-wrap justify-end gap-2 border-t border-[#eadfd3] pt-4"><button className="btn" disabled={busy} onClick={closeDialog}>انصراف</button><button className="btn btn-primary" disabled={busy} onClick={() => void createPurchase()}>{busy ? "در حال ثبت…" : "تأیید و ثبت خرید"}</button></footer>
      </div>
    </FormDialog>

    <FormDialog open={dialog === "payment"} onClose={closeDialog} closeDisabled={busy} width="sm" title="ثبت پرداخت تأمین‌کننده" description={paymentInvoice ? `ماندهٔ این فاکتور ${money(paymentInvoice.balance_due)} ریال است.` : undefined}>
      <div className="space-y-3">
        {formError && <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-900">{formError}</div>}
        <label className="block text-sm font-bold">مبلغ پرداخت (ریال)<input autoFocus className="btn mt-1 w-full" inputMode="numeric" placeholder="مثلاً ۵۰۰٬۰۰۰" value={paymentForm.amount} onChange={event => setPaymentForm({...paymentForm,amount:event.target.value})}/></label>
        <label className="block text-sm font-bold">روش پرداخت<select className="btn mt-1 w-full" value={paymentForm.method} onChange={event => setPaymentForm({...paymentForm,method:event.target.value as PaymentMethod,bank_account:""})}><option value="CASH">نقدی</option><option value="POS">کارت یا حساب بانکی</option></select></label>
        {paymentForm.method === "POS" && <label className="block text-sm font-bold">کارت یا حساب پرداخت‌کننده<select className="btn mt-1 w-full" value={paymentForm.bank_account} onChange={event => setPaymentForm({...paymentForm,bank_account:event.target.value})}><option value="">انتخاب کارت یا حساب</option>{branchAccounts.map(account => <option key={account.id} value={account.id}>{account.display_name}</option>)}</select>{!branchAccounts.length && <span className="mt-1 block text-xs text-amber-800">برای این شعبه کارت یا حساب فعال ثبت نشده است.</span>}</label>}
        <label className="block text-sm font-bold">شماره رسید یا یادداشت<input className="btn mt-1 w-full" placeholder="اختیاری" value={paymentForm.reference} onChange={event => setPaymentForm({...paymentForm,reference:event.target.value})}/></label>
        <footer className="mt-5 flex justify-end gap-2 border-t border-[#eadfd3] pt-4"><button className="btn" disabled={busy} onClick={closeDialog}>انصراف</button><button className="btn btn-primary" disabled={busy} onClick={() => void submitPayment()}>{busy ? "در حال ثبت…" : "تأیید پرداخت"}</button></footer>
      </div>
    </FormDialog>
  </div>;
}

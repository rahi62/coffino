"use client";

import {useEffect, useMemo, useState} from "react";
import FormDialog from "@/components/form-dialog";
import {LocalizedDateInput} from "@/components/localized-date-input";
import {api} from "@/lib/api";
import {formatLocalizedDate} from "@/lib/calendar";

type PurchaseRow = {inventory_item:string; quantity:string; unit_cost:string; lot_number:string; expires_at:string};
type Branch = {id:number; name:string; is_active:boolean};
type Supplier = {id:number; branch:number; name:string};
type InventoryItem = {id:number; branch:number; name:string; unit:string; lot_tracked:boolean};
type BankAccount = {id:number; branch:number; display_name:string; is_active:boolean};
type PurchaseItem = {id:number; inventory_name:string; inventory_unit:string; quantity:string; unit_cost:string};
type PurchaseInvoice = {id:number; branch:number; supplier:number; invoice_number:string; invoice_date:string; purchaser_name:string; created_by_name:string|null; status:string; supplier_name:string; total_amount:string; paid_amount:string; balance_due:string; items:PurchaseItem[]};
type PaymentMethod = "CASH" | "POS";
type Dialog = "purchase" | "payment" | null;
type InvoiceFilters = {search:string; supplier:string; status:string; start:string; end:string};

const emptyRow = (): PurchaseRow => ({inventory_item:"", quantity:"1", unit_cost:"0", lot_number:"", expires_at:""});
const money = (value:string|number) => Number(value || 0).toLocaleString("fa-IR");
const quantity = (value:string|number) => Number(value || 0).toLocaleString("fa-IR", {maximumFractionDigits:3});
const unitLabel = (unit:string) => ({gram:"گرم", kilogram:"کیلوگرم", piece:"عدد", liter:"لیتر", milliliter:"میلی‌لیتر"}[unit] || unit || "واحد");
const statusLabel:Record<string,string> = {DRAFT:"پیش‌نویس", POSTED:"ثبت‌شده", CANCELLED:"لغو‌شده"};
const today = () => new Date().toISOString().slice(0,10);

export default function Purchasing(){
  const [suppliers,setSuppliers] = useState<Supplier[]>([]);
  const [inventory,setInventory] = useState<InventoryItem[]>([]);
  const [invoices,setInvoices] = useState<PurchaseInvoice[]>([]);
  const [branches,setBranches] = useState<Branch[]>([]);
  const [accounts,setAccounts] = useState<BankAccount[]>([]);
  const [selectedBranchId,setSelectedBranchId] = useState<number|"">("");
  const [supplier,setSupplier] = useState("");
  const [purchaserName,setPurchaserName] = useState("");
  const [invoiceNumber,setInvoiceNumber] = useState("");
  const [invoiceDate,setInvoiceDate] = useState(today);
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
  const [filters,setFilters] = useState<InvoiceFilters>({search:"",supplier:"",status:"",start:"",end:""});

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
  const inventoryById = useMemo(() => new Map(branchInventory.map(item => [item.id,item])), [branchInventory]);
  const filteredInvoices = useMemo(() => branchInvoices.filter(invoice => {
    const searchable = `${invoice.supplier_name} ${invoice.purchaser_name || ""} ${invoice.created_by_name || ""} ${invoice.invoice_number || ""}`.toLocaleLowerCase("fa-IR");
    const invoiceDate = invoice.invoice_date.slice(0,10);
    return (!filters.search || searchable.includes(filters.search.trim().toLocaleLowerCase("fa-IR")))
      && (!filters.supplier || String(invoice.supplier) === filters.supplier)
      && (!filters.status || invoice.status === filters.status)
      && (!filters.start || invoiceDate >= filters.start.slice(0,10))
      && (!filters.end || invoiceDate <= filters.end.slice(0,10));
  }), [branchInvoices,filters]);
  const total = useMemo(() => rows.reduce((sum,row) => sum + Number(row.quantity || 0) * Number(row.unit_cost || 0), 0), [rows]);

  const closeDialog = () => {
    if (!busy) { setDialog(null); setFormError(""); setPaymentInvoice(null); }
  };
  const resetPurchase = () => {
    setSupplier(""); setPurchaserName(""); setInvoiceNumber(""); setInvoiceDate(today()); setPaid("0"); setMethod("CASH"); setBankAccount(""); setRows([emptyRow()]); setFormError("");
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
    if (!purchaserName.trim()) { setFormError("نام شخص خریدار را وارد کنید."); return; }
    if (!invoiceDate) { setFormError("تاریخ فاکتور را انتخاب کنید."); return; }
    if (!items.length) { setFormError("حداقل یک مادهٔ اولیه به فاکتور اضافه کنید."); return; }
    if (!items.every(row => Number(row.quantity) > 0 && Number(row.unit_cost) >= 0)) { setFormError("تعداد و بهای واحد هر ردیف را به‌درستی وارد کنید."); return; }
    if (Number(paid) < 0 || !validateBankAccount(method, bankAccount)) return;
    setBusy(true); setFormError("");
    try {
      await api("/purchases/create/", {
        method:"POST",
        body:JSON.stringify({
          branch:selectedBranchId, supplier:Number(supplier), invoice_date:invoiceDate,
          purchaser_name:purchaserName.trim(), invoice_number:invoiceNumber.trim(),
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

    <section className="card overflow-hidden">
      <div className="border-b border-[#eadfd3] p-4"><h2 className="text-xl font-black">جدول خریدها</h2><p className="mt-1 text-sm text-[#8d8178]">فاکتورهای شعبهٔ انتخاب‌شده را بر اساس تاریخ، تأمین‌کننده، وضعیت یا نام خریدار پیدا کنید.</p></div>
      <div className="grid gap-3 border-b border-[#eadfd3] p-4 sm:grid-cols-2 xl:grid-cols-6">
        <label className="text-sm font-bold xl:col-span-2">جست‌وجو<input className="btn mt-1 w-full" placeholder="تأمین‌کننده، خریدار یا شماره فاکتور" value={filters.search} onChange={event => setFilters({...filters,search:event.target.value})}/></label>
        <label className="text-sm font-bold">تأمین‌کننده<select className="btn mt-1 w-full" value={filters.supplier} onChange={event => setFilters({...filters,supplier:event.target.value})}><option value="">همه</option>{branchSuppliers.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
        <label className="text-sm font-bold">وضعیت<select className="btn mt-1 w-full" value={filters.status} onChange={event => setFilters({...filters,status:event.target.value})}><option value="">همه</option><option value="POSTED">ثبت‌شده</option><option value="DRAFT">پیش‌نویس</option><option value="CANCELLED">لغو‌شده</option></select></label>
        <label className="text-sm font-bold">از تاریخ<LocalizedDateInput value={filters.start} onChange={start => setFilters({...filters,start})}/></label>
        <label className="text-sm font-bold">تا تاریخ<LocalizedDateInput value={filters.end} onChange={end => setFilters({...filters,end})}/></label>
        <div className="flex items-end"><button className="btn w-full" onClick={() => setFilters({search:"",supplier:"",status:"",start:"",end:""})}>پاک‌کردن فیلترها</button></div>
      </div>
      <div className="overflow-x-auto"><table className="w-full min-w-[1120px] text-sm"><thead className="bg-[#f7f0e8]"><tr><th className="p-3 text-right">تاریخ</th><th className="text-right">شماره فاکتور</th><th className="text-right">تأمین‌کننده</th><th className="text-right">خریدار</th><th className="text-right">اقلام و مقدار</th><th className="text-right">جمع کل</th><th className="text-right">مانده</th><th className="text-right">وضعیت</th><th className="pl-3 text-right">عملیات</th></tr></thead><tbody>{filteredInvoices.length ? filteredInvoices.map(invoice => <tr className="border-t border-[#f0e8df]" key={invoice.id}><td className="whitespace-nowrap p-3">{formatLocalizedDate(`${invoice.invoice_date}T12:00:00`)}</td><td>{invoice.invoice_number || "—"}</td><td className="font-bold">{invoice.supplier_name}</td><td>{invoice.purchaser_name || invoice.created_by_name || "—"}</td><td><div className="min-w-52 space-y-1">{invoice.items.map(item => <span className="block" key={item.id}>{item.inventory_name}: {quantity(item.quantity)} {unitLabel(item.inventory_unit)}</span>)}</div></td><td className="whitespace-nowrap font-bold">{money(invoice.total_amount)}</td><td className="whitespace-nowrap">{money(invoice.balance_due)}</td><td><span className={invoice.status === "POSTED" ? "badge bg-emerald-100 text-emerald-800" : "badge"}>{statusLabel[invoice.status] || invoice.status}</span></td><td className="pl-3">{Number(invoice.balance_due) > 0 && invoice.status === "POSTED" ? <button className="btn text-xs" onClick={() => openPayment(invoice)}>ثبت پرداخت</button> : "—"}</td></tr>) : <tr><td colSpan={9} className="p-10 text-center text-[#8d8178]">{branchInvoices.length ? "فاکتوری مطابق فیلترها پیدا نشد." : "برای شعبهٔ انتخاب‌شده فاکتور خریدی ثبت نشده است."}</td></tr>}</tbody></table></div>
    </section>

    <FormDialog open={dialog === "purchase"} onClose={closeDialog} closeDisabled={busy} width="lg" title="ثبت فاکتور خرید" description="پس از ثبت، موجودی مواد اولیه به‌روزرسانی می‌شود؛ اطلاعات را پیش از تأیید بررسی کنید.">
      <div className="space-y-4">
        {formError && <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-900">{formError}</div>}
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <label className="text-sm font-bold">تأمین‌کننده<select autoFocus className="btn mt-1 w-full" value={supplier} onChange={event => setSupplier(event.target.value)}><option value="">انتخاب تأمین‌کننده</option>{branchSuppliers.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
          <label className="text-sm font-bold">نام خریدار<input className="btn mt-1 w-full" placeholder="مثلاً مریم رضایی" value={purchaserName} onChange={event => setPurchaserName(event.target.value)}/></label>
          <label className="text-sm font-bold">تاریخ فاکتور<LocalizedDateInput value={invoiceDate} onChange={setInvoiceDate}/></label>
          <label className="text-sm font-bold">شماره فاکتور یا رسید<input className="btn mt-1 w-full" placeholder="اختیاری" value={invoiceNumber} onChange={event => setInvoiceNumber(event.target.value)}/></label>
          <label className="text-sm font-bold">پرداخت اولیه (ریال)<input className="btn mt-1 w-full" inputMode="numeric" placeholder="مثلاً ۵۰۰٬۰۰۰" value={paid} onChange={event => setPaid(event.target.value)}/></label>
          <label className="text-sm font-bold">روش پرداخت<select className="btn mt-1 w-full" value={method} onChange={event => { setMethod(event.target.value as PaymentMethod); setBankAccount(""); }}><option value="CASH">نقدی</option><option value="POS">کارت یا حساب بانکی</option></select></label>
          {method === "POS" && <label className="text-sm font-bold sm:col-span-2 lg:col-span-3">کارت یا حساب پرداخت‌کننده<select className="btn mt-1 w-full" value={bankAccount} onChange={event => setBankAccount(event.target.value)}><option value="">انتخاب کارت یا حساب</option>{branchAccounts.map(account => <option key={account.id} value={account.id}>{account.display_name}</option>)}</select>{!branchAccounts.length && <span className="mt-1 block text-xs text-amber-800">کارت یا حساب فعالی برای این شعبه ثبت نشده است. ابتدا از بخش «کارت‌ها و حساب‌های بانکی» آن را تعریف کنید.</span>}</label>}
        </div>
        <div className="overflow-x-auto rounded-xl border border-[#eadfd3]"><div className="min-w-[860px] space-y-2 p-3">
          <div className="grid grid-cols-[minmax(190px,1fr)_120px_130px_150px_190px_42px] gap-2 px-1 text-xs font-bold text-[#8d8178]"><span>مادهٔ اولیه</span><span>مقدار خرید</span><span>بهای هر واحد</span><span>شماره سری ساخت</span><span>تاریخ انقضا</span><span aria-label="حذف ردیف" /></div>
          {rows.map((row,index) => <div className="grid grid-cols-[minmax(190px,1fr)_120px_130px_150px_190px_42px] gap-2" key={index}>
            <select className="btn" value={row.inventory_item} onChange={event => setRow(index,"inventory_item",event.target.value)}><option value="">انتخاب مادهٔ اولیه</option>{branchInventory.map(item => <option value={item.id} key={item.id}>{item.name} — {unitLabel(item.unit)}{item.lot_tracked ? " · سری ساخت" : ""}</option>)}</select>
            <div className="relative"><input className="btn w-full pl-11" inputMode="decimal" placeholder="مثلاً ۵۰۰۰" value={row.quantity} onChange={event => setRow(index,"quantity",event.target.value)}/><span className="pointer-events-none absolute inset-y-0 left-2 flex items-center text-xs text-[#8d8178]">{unitLabel(inventoryById.get(Number(row.inventory_item))?.unit || "")}</span></div>
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

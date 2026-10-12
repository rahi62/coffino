"use client";

import {useEffect, useMemo, useState} from "react";
import FormDialog from "@/components/form-dialog";
import ThermalReceiptDesigner, {defaultReceiptLayout, DocumentType, ThermalLayout, ThermalReceiptPreview} from "@/components/thermal-receipt-designer";
import {api} from "@/lib/api";
import {label} from "@/lib/i18n";
import Link from "next/link";


type Device = {id: number; branch: number; name: string; system_name: string; kind: string; paper_width: number; is_active: boolean};
type Template = {
  id: number; branch: number; name: string; document_type: DocumentType; header: string; footer: string;
  show_tax: boolean; show_service_charge: boolean; show_customer: boolean; is_default: boolean; layout?: ThermalLayout;
};
type TemplateForm = Omit<Template, "id" | "branch">;

const newTemplate = (): TemplateForm => ({
  name: "", document_type: "RECEIPT", header: "", footer: "", show_tax: true,
  show_service_charge: true, show_customer: true, is_default: true, layout: defaultReceiptLayout("RECEIPT"),
});
const deviceEmpty = {name: "", system_name: "", kind: "RECEIPT", paper_width: "80", is_active: true};
const typeLabel: Record<string, string> = {RECEIPT: "رسید مشتری", KITCHEN: "تیکت آشپزخانه", BAR: "تیکت بار"};

export default function Printing() {
  const [permissions,setPermissions]=useState<Record<string,boolean>|null>(null);
  const [permissionsLoading,setPermissionsLoading]=useState(true);
  const mayManage=permissions?.["printing.manage"]===true;
  const mayUse=permissions?.["printing.use"]===true;
  useEffect(()=>{api<{permissions:Record<string,boolean>}>("/permissions/me/").then(x=>setPermissions(x.permissions)).catch(()=>setPermissions({})).finally(()=>setPermissionsLoading(false))},[]);
  const [osPrinters, setOsPrinters] = useState<any[]>([]);
  const [devices, setDevices] = useState<Device[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [jobs, setJobs] = useState<any[]>([]);
  const [branches, setBranches] = useState<any[]>([]);
  const [branch, setBranch] = useState("");
  const [receipt, setReceipt] = useState("");
  const [kitchen, setKitchen] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [deviceOpen, setDeviceOpen] = useState(false);
  const [templateOpen, setTemplateOpen] = useState(false);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [deviceForm, setDeviceForm] = useState<any>(deviceEmpty);
  const [templateForm, setTemplateForm] = useState<TemplateForm>(newTemplate);
  const [editingTemplate, setEditingTemplate] = useState<Template | null>(null);

  const selectedBranch = branch || String(branches[0]?.id || "");
  const branchDevices = useMemo(() => devices.filter((device) => String(device.branch) === selectedBranch), [devices, selectedBranch]);
  const branchTemplates = useMemo(() => templates.filter((template) => String(template.branch) === selectedBranch), [templates, selectedBranch]);
  const activeReceiptDevice = branchDevices.find((device) => device.system_name === receipt) || branchDevices.find((device) => device.kind === "RECEIPT");
  const receiptTemplate = branchTemplates.find((template) => template.document_type === "RECEIPT" && template.is_default) || branchTemplates.find((template) => template.document_type === "RECEIPT");

  const load = async () => {
    try {
      const [nextDevices, nextTemplates, nextJobs, nextBranches] = await Promise.all([
        api<Device[]>("/printers/"), api<Template[]>("/print-templates/"), api<any[]>("/print-jobs/"), api<any[]>("/branches/"),
      ]);
      setDevices(nextDevices);
      setTemplates(nextTemplates);
      setJobs(nextJobs);
      setBranches(nextBranches);
      if (!branch) {const stored=Number(localStorage.getItem("cafino_settings_branch")||0);const candidate=nextBranches.find(x=>x.id===stored)||nextBranches[0];if(candidate)setBranch(String(candidate.id));}
      const currentId=branch||String(nextBranches.find(x=>x.id===Number(localStorage.getItem("cafino_settings_branch")||0))?.id||nextBranches[0]?.id||"");
      setReceipt(localStorage.getItem(`cafino_receipt_branch_${currentId}`)||localStorage.getItem("cafino_receipt_printer") || "");
      setKitchen(localStorage.getItem("cafino_kitchen_printer") || "");
      const desktop = (window as any).cafino;
      if (desktop?.listPrinters) setOsPrinters(await desktop.listPrinters());
    } catch (error: any) {
      setMessage(error.message || "دریافت تنظیمات چاپ انجام نشد.");
    }
  };

  useEffect(() => { if (!permissionsLoading && (mayManage || mayUse)) void load(); }, [permissionsLoading, mayManage, mayUse]);

  const closeDevice = () => { if (!busy) { setDeviceOpen(false); setDeviceForm(deviceEmpty); } };
  const closeTemplate = () => { if (!busy) { setTemplateOpen(false); setEditingTemplate(null); setTemplateForm(newTemplate()); } };
  const saveLocal = () => {
    localStorage.setItem("cafino_receipt_printer", receipt);
    localStorage.setItem("cafino_kitchen_printer", kitchen);
    localStorage.setItem("cafino_receipt_paper_width", String(activeReceiptDevice?.paper_width || 80));
    setMessage("انتخاب چاپگرهای محلی ذخیره شد.");
  };
  const openDevice = (printer?: any) => {
    setDeviceForm(printer ? {...deviceEmpty, name: printer.displayName || printer.name, system_name: printer.name} : deviceEmpty);
    setDeviceOpen(true);
  };
  const saveDevice = async () => {
    if (!mayManage || !selectedBranch || !deviceForm.name.trim()) return;
    setBusy(true);
    try {
      await api("/printers/", {method: "POST", body: JSON.stringify({...deviceForm, branch: Number(selectedBranch), paper_width: Number(deviceForm.paper_width)})});
      setMessage("دستگاه چاپ ثبت شد.");
      closeDevice();
      await load();
    } catch (error: any) {
      setMessage(error.message || "ثبت دستگاه چاپ انجام نشد.");
    } finally { setBusy(false); }
  };
  const openTemplate = (template?: Template) => {
    setEditingTemplate(template || null);
    setTemplateForm(template ? {
      name: template.name, document_type: template.document_type, header: template.header || "", footer: template.footer || "",
      show_tax: template.show_tax, show_service_charge: template.show_service_charge, show_customer: template.show_customer,
      is_default: template.is_default, layout: template.layout || defaultReceiptLayout(template.document_type),
    } : newTemplate());
    setTemplateOpen(true);
  };
  const changeDocumentType = (documentType: DocumentType) => {
    setTemplateForm((current) => ({
      ...current,
      document_type: documentType,
      layout: {...defaultReceiptLayout(documentType), paper_width: current.layout?.paper_width === 58 ? 58 : 80},
    }));
  };
  const saveTemplate = async () => {
    if (!mayManage || !selectedBranch || !templateForm.name.trim()) return;
    setBusy(true);
    try {
      const body = {...templateForm, branch: Number(selectedBranch), name: templateForm.name.trim()};
      if (editingTemplate) await api(`/print-templates/${editingTemplate.id}/`, {method: "PATCH", body: JSON.stringify(body)});
      else await api("/print-templates/", {method: "POST", body: JSON.stringify(body)});
      setMessage(editingTemplate ? "قالب چاپ به‌روزرسانی شد." : "قالب چاپ ثبت شد.");
      closeTemplate();
      await load();
    } catch (error: any) {
      setMessage(error.message || "ذخیره قالب چاپ انجام نشد.");
    } finally { setBusy(false); }
  };
  const printTest = async () => {
    const desktop = (window as any).cafino;
    if (!desktop?.printHtml) {
      setMessage("چاپ مستقیم فقط در برنامهٔ دسکتاپ کافینو فعال است؛ پیش‌نمایش را در همین صفحه بررسی کنید.");
      return;
    }
    const html = `<html dir="rtl"><head><meta charset="utf-8"></head><body>${document.getElementById("thermal-preview")?.innerHTML || ""}</body></html>`;
    const result = await desktop.printHtml(html, receipt);
    setMessage(result?.ok ? "برگهٔ آزمایشی به چاپگر ارسال شد." : `چاپ آزمایشی انجام نشد: ${result?.error || "خطای نامشخص"}`);
  };

  if (permissionsLoading) return <div role="status" className="card p-5">در حال بررسی دسترسی چاپ…</div>;
  if (!mayManage && !mayUse) return <section role="alert" className="card p-5"><h1 className="text-xl font-black">چاپ در دسترس نیست</h1><p className="mt-2">برای استفاده از چاپ، ماژول چاپ و مجوز مربوط باید فعال باشند.</p><Link href="/settings/business" className="btn mt-4 inline-flex">بررسی قابلیت‌های کسب‌وکار</Link></section>;
  return <div className="space-y-5">
    <header className="flex flex-col gap-3 rounded-[22px] border border-[#eadfd3] bg-[#fffdf9] p-5 shadow-sm sm:flex-row sm:items-end sm:justify-between">
      <div><p className="mb-1 text-sm font-bold text-[#b9792d]">تنظیمات فروش</p><h1 className="text-3xl font-black">مرکز چاپ و فاکتور ساز</h1><p className="mt-2 text-[#8d8178]">چاپگر حرارتی و قالب فیش مشتری، آشپزخانه و بار را برای هر شعبه تنظیم کنید.</p></div>
      <div className="flex gap-2">{mayManage&&<><button className="btn" onClick={() => openTemplate()}>قالب جدید</button><button className="btn btn-primary" onClick={() => openDevice()}>ثبت چاپگر</button></>}</div>
    </header>
    {!mayManage&&<div role="alert" className="card p-4">حساب فعلی اجازه ساخت یا تغییر قالب چاپ را ندارد. برای مدیریت چاپگر و قالب، مجوز مدیریت چاپ لازم است.</div>}
    {message && <div role="status" className="card border-r-4 border-r-[#b9792d] p-4">{message}</div>}

    <section className="card flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
      <label className="text-sm font-bold">شعبه<select className="btn mr-2 min-w-48" value={selectedBranch} onChange={(event) => setBranch(event.target.value)}>{branches.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
      <button className="btn" onClick={() => setPreviewOpen(true)}>پیش‌نمایش فیش حرارتی</button>
    </section>

    <section className="grid gap-4 lg:grid-cols-2">
      <div className="card p-5">
        <h2 className="font-black text-lg">انتخاب چاپگر محلی</h2><p className="mt-1 text-sm text-[#8d8178]">در برنامهٔ دسکتاپ، چاپ بدون نمایش پنجرهٔ مرورگر به چاپگر انتخاب‌شده ارسال می‌شود.</p>
        {osPrinters.length ? <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <label className="text-sm font-bold">رسید مشتری<select className="btn mt-1 w-full" value={receipt} onChange={(event) => setReceipt(event.target.value)}><option value="">چاپگر پیش‌فرض سیستم</option>{osPrinters.map((printer) => <option key={printer.name} value={printer.name}>{printer.displayName || printer.name}</option>)}</select></label>
          <label className="text-sm font-bold">تیکت آشپزخانه<select className="btn mt-1 w-full" value={kitchen} onChange={(event) => setKitchen(event.target.value)}><option value="">چاپگر پیش‌فرض سیستم</option>{osPrinters.map((printer) => <option key={printer.name} value={printer.name}>{printer.displayName || printer.name}</option>)}</select></label>
        </div> : <p className="mt-4 rounded-xl bg-[#f7f0e8] p-3 text-sm text-[#8d8178]">چاپگر محلی فقط در برنامهٔ دسکتاپ کافینو نمایش داده می‌شود.</p>}
        <div className="mt-4 flex flex-wrap gap-2"><button className="btn btn-primary" onClick={saveLocal} disabled={!osPrinters.length}>ذخیره انتخاب</button><button className="btn" disabled={!osPrinters.length} onClick={() => void printTest()}>چاپ آزمایشی</button></div>
      </div>
      <div className="card p-5">
        <div className="flex items-center justify-between"><h2 className="font-black text-lg">چاپگرهای ثبت‌شدهٔ شعبه</h2><span className="badge">{branchDevices.length.toLocaleString("fa-IR")} دستگاه</span></div>
        <div className="mt-3 space-y-2">{branchDevices.length ? branchDevices.map((device) => <div className="flex items-center justify-between rounded-xl bg-[#f7f0e8] p-3 text-sm" key={device.id}><div><b>{device.name}</b><span className="mr-2 text-[#8d8178]">{typeLabel[device.kind] || device.kind} · {device.paper_width} میلی‌متر</span></div><span className={device.is_active ? "badge bg-emerald-100 text-emerald-800" : "badge"}>{device.is_active ? "فعال" : "غیرفعال"}</span></div>) : <p className="text-sm text-[#8d8178]">برای این شعبه هنوز چاپگری ثبت نشده است.</p>}</div>
      </div>
    </section>

    <section className="card p-4"><label className="block text-sm font-bold">چاپگر رسید شعبه<select className="btn mt-2 w-full" value={receipt} onChange={e=>setReceipt(e.target.value)}><option value="">انتخاب چاپگر ثبت‌شده</option>{branchDevices.filter(device=>device.is_active&&device.kind==="RECEIPT").map(device=><option key={device.id} value={device.system_name}>{device.name}</option>)}</select></label><p className="mt-2 text-xs text-[#8d8178]">این انتخاب فقط در همین مرورگر ذخیره می‌شود؛ چاپ مستقیم و شناسایی چاپگر فیزیکی ویندوز فقط در نسخه دسکتاپ امکان‌پذیر است.</p><button type="button" className="btn mt-3 min-h-11" disabled={!selectedBranch||!receipt} onClick={()=>{localStorage.setItem(`cafino_receipt_branch_${selectedBranch}`,receipt);setMessage("انتخاب چاپگر ثبت‌شده برای این شعبه در مرورگر ذخیره شد؛ برای چاپ مستقیم از نسخه دسکتاپ استفاده کنید.");}}>ذخیره انتخاب شعبه در این مرورگر</button></section>
    <section className="card overflow-hidden">
      <div className="flex items-center justify-between border-b border-[#eadfd3] p-4"><div><h2 className="font-black text-lg">قالب‌های فیش و تیکت</h2><p className="mt-1 text-sm text-[#8d8178]">قالب پیش‌فرض هر نوع سند، خودکار در صف چاپ سفارش قرار می‌گیرد.</p></div>{mayManage&&<button className="btn" onClick={() => openTemplate()}>افزودن قالب</button>}</div>
      <div className="grid gap-3 p-4 md:grid-cols-2 xl:grid-cols-3">{branchTemplates.length ? branchTemplates.map((template) => <article className="rounded-2xl border border-[#eadfd3] p-4" key={template.id}><div className="flex items-start justify-between gap-2"><div><b>{template.name}</b><span className="mt-1 block text-sm text-[#8d8178]">{typeLabel[template.document_type]}</span></div>{template.is_default && <span className="badge bg-emerald-100 text-emerald-800">پیش‌فرض</span>}</div><p className="mt-3 line-clamp-2 min-h-10 text-sm text-[#8d8178]">{template.header || template.footer || "بدون متن آغاز یا پایان"}</p><div className="mt-3 flex flex-wrap gap-1 text-xs"><span className="badge">{template.layout?.paper_width || 80} میلی‌متر</span><span className="badge">{template.layout?.blocks?.length || defaultReceiptLayout(template.document_type).blocks.length} بخش</span></div>{mayManage&&<button className="btn mt-4 w-full" onClick={() => openTemplate(template)}>ویرایش قالب</button>}</article>) : <div className="col-span-full p-8 text-center text-[#8d8178]">هنوز قالبی برای این شعبه ساخته نشده است؛ رسید استاندارد کافینو چاپ می‌شود.</div>}</div>
    </section>

    <section className="card p-4"><h2 className="font-black text-lg">تاریخچهٔ صف چاپ</h2><div className="mt-3 space-y-2">{jobs.filter((job) => String(job.branch) === selectedBranch).slice(0, 20).map((job) => <div className="flex justify-between border-t border-[#f0e8df] py-2 text-sm" key={job.id}><span>{typeLabel[job.document_type] || job.document_type} · {job.entity_type} {job.entity_id}</span><span className="badge">{label(job.status)}</span></div>)}</div></section>

    <FormDialog open={deviceOpen} onClose={closeDevice} closeDisabled={busy} width="sm" title="ثبت چاپگر" description="نام چاپگر را برای استفاده در این شعبه ثبت کنید.">
      <div className="space-y-3"><label className="block text-sm font-bold">نام نمایشی<input autoFocus className="btn mt-1 w-full" placeholder="مثلاً فیش صندوق" value={deviceForm.name} onChange={(event) => setDeviceForm({...deviceForm, name: event.target.value})} /></label><label className="block text-sm font-bold">نام سیستمی چاپگر<input className="btn mt-1 w-full" placeholder="نام چاپگر در سیستم‌عامل" value={deviceForm.system_name} onChange={(event) => setDeviceForm({...deviceForm, system_name: event.target.value})} /></label><div className="grid gap-3 sm:grid-cols-2"><label className="block text-sm font-bold">کاربرد<select className="btn mt-1 w-full" value={deviceForm.kind} onChange={(event) => setDeviceForm({...deviceForm, kind: event.target.value})}><option value="RECEIPT">رسید مشتری</option><option value="KITCHEN">آشپزخانه</option><option value="BAR">بار</option></select></label><label className="block text-sm font-bold">عرض کاغذ<select className="btn mt-1 w-full" value={deviceForm.paper_width} onChange={(event) => setDeviceForm({...deviceForm, paper_width: event.target.value})}><option value="80">۸۰ میلی‌متر</option><option value="58">۵۸ میلی‌متر</option></select></label></div></div>
      <footer className="mt-5 flex justify-end gap-2 border-t border-[#eadfd3] pt-4"><button className="btn" disabled={busy} onClick={closeDevice}>انصراف</button><button className="btn btn-primary" disabled={busy || !deviceForm.name.trim()} onClick={() => void saveDevice()}>{busy ? "در حال ثبت…" : "ثبت چاپگر"}</button></footer>
    </FormDialog>

    <FormDialog open={templateOpen} onClose={closeTemplate} closeDisabled={busy} width="lg" title={editingTemplate ? "ویرایش قالب چاپ" : "ساخت قالب چاپ"} description="قالب پیش‌فرض هر نوع فیش، هنگام چاپ سفارش خودکار استفاده می‌شود.">
      <div className="grid gap-3 sm:grid-cols-2"><label className="block text-sm font-bold sm:col-span-2">نام قالب<input autoFocus className="btn mt-1 w-full" placeholder="مثلاً رسید سادهٔ صندوق" value={templateForm.name} onChange={(event) => setTemplateForm({...templateForm, name: event.target.value})} /></label><label className="block text-sm font-bold">نوع سند<select className="btn mt-1 w-full" value={templateForm.document_type} onChange={(event) => changeDocumentType(event.target.value as DocumentType)}><option value="RECEIPT">رسید مشتری</option><option value="KITCHEN">تیکت آشپزخانه</option><option value="BAR">تیکت بار</option></select></label><label className="flex items-end gap-2 text-sm font-bold"><input type="checkbox" checked={templateForm.is_default} onChange={(event) => setTemplateForm({...templateForm, is_default: event.target.checked})} /> قالب پیش‌فرض این نوع باشد</label><label className="block text-sm font-bold sm:col-span-2">متن آغاز فیش<textarea className="btn mt-1 min-h-20 w-full" placeholder="مثلاً نام مجموعه یا پیام خوش‌آمدگویی" value={templateForm.header} onChange={(event) => setTemplateForm({...templateForm, header: event.target.value})} /></label><label className="block text-sm font-bold sm:col-span-2">متن پایان فیش<textarea className="btn mt-1 min-h-20 w-full" placeholder="مثلاً سپاس از خرید شما" value={templateForm.footer} onChange={(event) => setTemplateForm({...templateForm, footer: event.target.value})} /></label><div className="sm:col-span-2 flex flex-wrap gap-4"><label className="flex gap-2 text-sm"><input type="checkbox" checked={templateForm.show_customer} onChange={(event) => setTemplateForm({...templateForm, show_customer: event.target.checked})} /> نمایش مشتری</label><label className="flex gap-2 text-sm"><input type="checkbox" checked={templateForm.show_tax} onChange={(event) => setTemplateForm({...templateForm, show_tax: event.target.checked})} /> نمایش مالیات</label><label className="flex gap-2 text-sm"><input type="checkbox" checked={templateForm.show_service_charge} onChange={(event) => setTemplateForm({...templateForm, show_service_charge: event.target.checked})} /> نمایش حق سرویس</label></div>
        <ThermalReceiptDesigner value={templateForm.layout} onChange={(layout) => setTemplateForm({...templateForm, layout})} type={templateForm.document_type} template={templateForm} />
      </div>
      <footer className="mt-5 flex justify-end gap-2 border-t border-[#eadfd3] pt-4"><button className="btn" disabled={busy} onClick={closeTemplate}>انصراف</button><button className="btn btn-primary" disabled={busy || !templateForm.name.trim()} onClick={() => void saveTemplate()}>{busy ? "در حال ذخیره…" : "ذخیره قالب"}</button></footer>
    </FormDialog>

    <FormDialog open={previewOpen} onClose={() => setPreviewOpen(false)} width="sm" title="پیش‌نمایش فیش حرارتی" description={`${receiptTemplate?.layout?.paper_width || activeReceiptDevice?.paper_width || 80} میلی‌متر؛ قالب پیش‌فرض رسید مشتری`}>
      <ThermalReceiptPreview id="thermal-preview" type="RECEIPT" layout={receiptTemplate?.layout || {...defaultReceiptLayout("RECEIPT"), paper_width: activeReceiptDevice?.paper_width === 58 ? 58 : 80}} template={receiptTemplate} />
      <footer className="mt-5 flex justify-end gap-2"><button className="btn" onClick={() => setPreviewOpen(false)}>بازگشت</button><button className="btn btn-primary" onClick={() => void printTest()}>چاپ آزمایشی</button></footer>
    </FormDialog>
  </div>;
}

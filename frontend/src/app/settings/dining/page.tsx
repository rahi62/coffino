"use client";

import {FormEvent, useEffect, useState} from "react";
import FormDialog from "@/components/form-dialog";
import {useSettings} from "@/components/settings/settings-context";
import {api} from "@/lib/api";

type Hall = {id:number; branch:number; name:string};
type DiningTable = {id:number; hall:number; number:string; capacity:number; status:string};
const statuses:Record<string,string> = {FREE:"آزاد", OCCUPIED:"اشغال", RESERVED:"رزرو شده", CLEANING:"نیازمند نظافت"};

export default function DiningSettings() {
  const {selectedBranch} = useSettings();
  const [halls, setHalls] = useState<Hall[]>([]);
  const [tables, setTables] = useState<DiningTable[]>([]);
  const [message, setMessage] = useState("");
  const [selectedHall, setSelectedHall] = useState("");
  const [hallName, setHallName] = useState("");
  const [tableForm, setTableForm] = useState({number:"", capacity:"4"});
  const [editingTable, setEditingTable] = useState<DiningTable|null>(null);
  const [hallDialog, setHallDialog] = useState(false);
  const [tableDialog, setTableDialog] = useState(false);
  const [saving, setSaving] = useState(false);

  const load = async () => {
    try { const [nextHalls, nextTables] = await Promise.all([api<Hall[]>("/halls/"), api<DiningTable[]>("/tables/")]); setHalls(nextHalls); setTables(nextTables); }
    catch (error:any) { setMessage(error.message || "دریافت اطلاعات سالن و میز انجام نشد."); }
  };
  useEffect(() => { void load(); }, []);
  const branchHalls = halls.filter(hall => hall.branch === selectedBranch?.id);
  useEffect(() => {
    if (branchHalls.length && !branchHalls.some(hall => String(hall.id) === selectedHall)) setSelectedHall(String(branchHalls[0].id));
    if (!branchHalls.length) setSelectedHall("");
  }, [branchHalls.length, selectedBranch?.id, selectedHall]);
  const hallTables = tables.filter(table => String(table.hall) === selectedHall);
  const closeHall = () => { setHallDialog(false); setHallName(""); };
  const closeTable = () => { setTableDialog(false); setEditingTable(null); setTableForm({number:"", capacity:"4"}); };
  const openNewTable = () => { setEditingTable(null); setTableForm({number:"", capacity:"4"}); setTableDialog(true); };
  const openEditTable = (table:DiningTable) => { setEditingTable(table); setTableForm({number:table.number, capacity:String(table.capacity)}); setTableDialog(true); };

  const addHall = async (event:FormEvent) => {
    event.preventDefault();
    if (!selectedBranch || !hallName.trim()) return;
    setSaving(true); setMessage("");
    try { const hall = await api<Hall>("/halls/", {method:"POST", body:JSON.stringify({branch:selectedBranch.id, name:hallName.trim()})}); closeHall(); setSelectedHall(String(hall.id)); setMessage("سالن جدید ساخته شد."); await load(); }
    catch (error:any) { setMessage(error.message || "ایجاد سالن انجام نشد."); }
    finally { setSaving(false); }
  };
  const saveTable = async (event:FormEvent) => {
    event.preventDefault();
    if (!selectedHall || !tableForm.number.trim()) { setMessage("شماره میز را وارد کنید."); return; }
    setSaving(true); setMessage("");
    const payload = {number:tableForm.number.trim(), capacity:Math.max(1, Number(tableForm.capacity || 1))};
    try {
      if (editingTable) { await api(`/tables/${editingTable.id}/`, {method:"PATCH", body:JSON.stringify(payload)}); setMessage("مشخصات میز ویرایش شد."); }
      else { await api("/tables/", {method:"POST", body:JSON.stringify({...payload, hall:Number(selectedHall), status:"FREE"})}); setMessage("میز جدید ساخته شد."); }
      closeTable(); await load();
    } catch (error:any) { setMessage(error.message || "ذخیرهٔ میز انجام نشد."); }
    finally { setSaving(false); }
  };

  if (!selectedBranch) return null;
  return <div className="space-y-5"><header className="flex flex-col gap-3 rounded-[22px] border border-[#eadfd3] bg-[#fffdf9] p-5 shadow-sm sm:flex-row sm:items-end sm:justify-between"><div><p className="mb-1 text-sm font-bold text-[#b9792d]">پیکربندی سرویس</p><h2 className="text-3xl font-black">سالن و میزها</h2><p className="mt-2 text-[#8d8178]">چیدمان هر شعبه را جدا از عملیات روزانهٔ باز و بسته‌کردن میزها تعریف کنید.</p></div><button type="button" className="btn btn-primary self-start" onClick={() => setHallDialog(true)}>افزودن سالن</button></header>{message && <div role="status" className="card border-r-4 border-r-[#b9792d] p-4">{message}</div>}<div className="grid gap-5 lg:grid-cols-[300px_minmax(0,1fr)]"><aside className="card overflow-hidden"><div className="border-b border-[#eadfd3] p-4"><h3 className="font-black">سالن‌های {selectedBranch.name}</h3><p className="mt-1 text-sm text-[#8d8178]">برای دیدن میزها یک سالن انتخاب کنید.</p></div><div className="p-2">{branchHalls.length ? branchHalls.map(hall => <button key={hall.id} className={`mb-1 w-full rounded-xl p-3 text-right transition ${String(hall.id) === selectedHall ? "bg-[#e8d8c2] font-black text-[#5c3518]" : "hover:bg-[#f7f0e8]"}`} onClick={() => setSelectedHall(String(hall.id))}>{hall.name}</button>) : <div className="p-4 text-sm text-[#8d8178]">هنوز سالنی ایجاد نشده است.</div>}</div></aside><section className="card overflow-hidden"><div className="flex flex-col gap-3 border-b border-[#eadfd3] p-4 sm:flex-row sm:items-center sm:justify-between"><div><h3 className="text-lg font-black">{selectedHall ? `میزهای ${branchHalls.find(hall => String(hall.id) === selectedHall)?.name || "سالن انتخاب‌شده"}` : "ابتدا یک سالن انتخاب کنید"}</h3><p className="mt-1 text-sm text-[#8d8178]">حذف سختِ میز بسته است تا تاریخچهٔ سفارش‌ها سالم بماند.</p></div><div className="flex gap-2"><a href="/tables" className="btn text-center">نمای عملیاتی میزها</a><button type="button" className="btn btn-primary" disabled={!selectedHall} onClick={openNewTable}>افزودن میز</button></div></div>{selectedHall ? hallTables.length ? <div className="grid gap-3 p-4 sm:grid-cols-2 xl:grid-cols-3">{hallTables.map(table => <article key={table.id} className="rounded-2xl border border-[#eadfd3] p-4"><div className="flex items-start justify-between gap-2"><div><div className="text-sm text-[#8d8178]">میز</div><h4 className="text-xl font-black">{table.number}</h4></div><span className={`badge ${table.status === "FREE" ? "bg-emerald-100 text-emerald-800" : table.status === "OCCUPIED" ? "bg-amber-100 text-amber-800" : ""}`}>{statuses[table.status] || table.status}</span></div><div className="mt-4 text-sm">ظرفیت: <b>{Number(table.capacity).toLocaleString("fa-IR")} نفر</b></div><button type="button" className="btn mt-4 w-full" onClick={() => openEditTable(table)}>ویرایش مشخصات</button></article>)}</div> : <div className="p-10 text-center"><b>هنوز میزی برای این سالن ایجاد نشده است.</b><p className="mt-2 text-sm text-[#8d8178]">با افزودن میز، در فروش داخل سالن قابل انتخاب می‌شود.</p></div> : <div className="p-10 text-center text-[#8d8178]">یک سالن را از ستون کناری انتخاب کنید.</div>}</section></div><FormDialog open={hallDialog} onClose={closeHall} closeDisabled={saving} width="sm" title="افزودن سالن" description={`این سالن فقط در شعبهٔ ${selectedBranch.name} ساخته می‌شود.`}><form className="space-y-4" onSubmit={addHall}><label className="block text-sm font-bold">نام سالن<input autoFocus className="btn mt-1 w-full" placeholder="مثلاً سالن اصلی" value={hallName} onChange={event => setHallName(event.target.value)}/></label><footer className="flex justify-end gap-2"><button type="button" className="btn" onClick={closeHall} disabled={saving}>انصراف</button><button className="btn btn-primary" disabled={saving || !hallName.trim()}>{saving ? "در حال ذخیره…" : "ثبت سالن"}</button></footer></form></FormDialog><FormDialog open={tableDialog} onClose={closeTable} closeDisabled={saving} width="sm" title={editingTable ? `ویرایش میز ${editingTable.number}` : "افزودن میز"} description="شماره و ظرفیت میز در فروش داخل سالن استفاده می‌شود."><form className="space-y-4" onSubmit={saveTable}><label className="block text-sm font-bold">شماره یا نام میز<input autoFocus className="btn mt-1 w-full" placeholder="مثلاً ۱۲ یا تراس ۱" value={tableForm.number} onChange={event => setTableForm({...tableForm, number:event.target.value})}/></label><label className="block text-sm font-bold">ظرفیت (نفر)<input className="btn mt-1 w-full" type="number" min="1" inputMode="numeric" placeholder="مثلاً ۴" value={tableForm.capacity} onChange={event => setTableForm({...tableForm, capacity:event.target.value})}/></label><footer className="flex justify-end gap-2"><button type="button" className="btn" onClick={closeTable} disabled={saving}>انصراف</button><button className="btn btn-primary" disabled={saving || !tableForm.number.trim()}>{saving ? "در حال ذخیره…" : editingTable ? "ذخیرهٔ تغییرات" : "ثبت میز"}</button></footer></form></FormDialog></div>;
}

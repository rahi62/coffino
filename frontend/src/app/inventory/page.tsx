"use client";

import Link from "next/link";
import {FormEvent, useEffect, useMemo, useState} from "react";
import FormDialog from "@/components/form-dialog";
import {api} from "@/lib/api";

type Branch = {id:number; name:string};
type MaterialCategory = {id:number; branch:number; name:string; sort_order:number; is_active:boolean};
type Material = {id:number; branch:number; name:string; category:string; material_category:number|null; material_category_name:string|null; unit:string; current_stock:number|string; minimum_stock:number|string; average_cost:number|string; item_code:string; lot_tracked:boolean; shelf_life_days:number; is_active:boolean; low_stock:boolean};
type MaterialForm = {name:string; material_category:string; unit:string; current_stock:string; minimum_stock:string; average_cost:string; item_code:string; shelf_life_days:string; lot_tracked:boolean};

const branchStorageKey = "cafino_settings_branch";
const emptyForm: MaterialForm = {name:"", material_category:"", unit:"gram", current_stock:"", minimum_stock:"", average_cost:"", item_code:"", shelf_life_days:"", lot_tracked:false};
const unitLabels:Record<string,string> = {gram:"گرم", kilogram:"کیلوگرم", milliliter:"میلی‌لیتر", liter:"لیتر", piece:"عدد", pack:"بسته"};

export default function Inventory() {
  const [materials, setMaterials] = useState<Material[]>([]);
  const [categories, setCategories] = useState<MaterialCategory[]>([]);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [selectedBranchId, setSelectedBranchId] = useState<number|null>(null);
  const [form, setForm] = useState<MaterialForm>(emptyForm);
  const [editing, setEditing] = useState<Material|null>(null);
  const [categoryName, setCategoryName] = useState("");
  const [editingCategory, setEditingCategory] = useState<MaterialCategory|null>(null);
  const [materialDialog, setMaterialDialog] = useState(false);
  const [categoryDialog, setCategoryDialog] = useState(false);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savingCategory, setSavingCategory] = useState(false);
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("all");

  const load = async () => {
    setLoading(true);
    try {
      const [nextMaterials, nextCategories, nextBranches] = await Promise.all([api<Material[]>("/inventory-items/"), api<MaterialCategory[]>("/ingredient-categories/"), api<Branch[]>("/branches/")]);
      setMaterials(nextMaterials); setCategories(nextCategories); setBranches(nextBranches);
      setSelectedBranchId(current => {
        if (current && nextBranches.some(branch => branch.id === current)) return current;
        const stored = Number(localStorage.getItem(branchStorageKey) || 0);
        return nextBranches.some(branch => branch.id === stored) ? stored : nextBranches[0]?.id || null;
      });
    } catch (error:any) { setMessage(error.message || "دریافت مواد اولیه انجام نشد."); }
    finally { setLoading(false); }
  };
  useEffect(() => { void load(); }, []);
  useEffect(() => { if (selectedBranchId) localStorage.setItem(branchStorageKey, String(selectedBranchId)); }, [selectedBranchId]);

  const selectedBranch = branches.find(branch => branch.id === selectedBranchId) || null;
  const branchMaterials = useMemo(() => materials.filter(material => material.branch === selectedBranchId), [materials, selectedBranchId]);
  const branchCategories = useMemo(() => categories.filter(category => category.branch === selectedBranchId), [categories, selectedBranchId]);
  const visibleMaterials = useMemo(() => branchMaterials.filter(material => {
    const needle = search.trim().toLocaleLowerCase("fa");
    const matchesSearch = !needle || [material.name, material.item_code, material.material_category_name || material.category || ""].some(value => value.toLocaleLowerCase("fa").includes(needle));
    return matchesSearch && (categoryFilter === "all" || material.material_category === Number(categoryFilter));
  }), [branchMaterials, categoryFilter, search]);
  const closeMaterial = () => { setMaterialDialog(false); setEditing(null); setForm(emptyForm); };
  const closeCategory = () => { setCategoryDialog(false); setEditingCategory(null); setCategoryName(""); };
  const openEdit = (material:Material) => { setEditing(material); setForm({name:material.name, material_category:material.material_category ? String(material.material_category) : "", unit:material.unit || "gram", current_stock:String(material.current_stock), minimum_stock:String(material.minimum_stock), average_cost:String(material.average_cost), item_code:material.item_code || "", shelf_life_days:String(material.shelf_life_days || 0), lot_tracked:material.lot_tracked}); setMaterialDialog(true); };
  const openCategoryEdit = (category:MaterialCategory) => { setEditingCategory(category); setCategoryName(category.name); setCategoryDialog(true); };

  const save = async (event:FormEvent) => {
    event.preventDefault();
    if (!selectedBranchId || !form.name.trim()) { setMessage("نام ماده اولیه را وارد کنید."); return; }
    setSaving(true); setMessage("");
    const payload = {name:form.name.trim(), material_category:form.material_category ? Number(form.material_category) : null, unit:form.unit, current_stock:Number(form.current_stock || 0), minimum_stock:Number(form.minimum_stock || 0), average_cost:Number(form.average_cost || 0), item_code:form.item_code.trim(), shelf_life_days:Number(form.shelf_life_days || 0), lot_tracked:form.lot_tracked};
    try {
      if (editing) { await api<Material>(`/inventory-items/${editing.id}/`, {method:"PATCH", body:JSON.stringify(payload)}); setMessage("ماده اولیه ویرایش شد."); }
      else { await api<Material>("/inventory-items/", {method:"POST", body:JSON.stringify({...payload, branch:selectedBranchId, is_active:true, last_purchase_cost:Number(form.average_cost || 0)})}); setMessage("ماده اولیه ایجاد شد و اکنون در رسپی‌ساز قابل انتخاب است."); }
      closeMaterial(); await load();
    } catch (error:any) { setMessage(error.message || "ذخیرهٔ ماده اولیه انجام نشد."); }
    finally { setSaving(false); }
  };
  const saveCategory = async (event:FormEvent) => {
    event.preventDefault();
    if (!selectedBranchId || !categoryName.trim()) return;
    setSavingCategory(true); setMessage("");
    try {
      if (editingCategory) { await api<MaterialCategory>(`/ingredient-categories/${editingCategory.id}/`, {method:"PATCH", body:JSON.stringify({name:categoryName.trim()})}); setMessage("دستهٔ مواد اولیه ویرایش شد."); }
      else { await api<MaterialCategory>("/ingredient-categories/", {method:"POST", body:JSON.stringify({branch:selectedBranchId, name:categoryName.trim(), sort_order:branchCategories.length, is_active:true})}); setMessage("دستهٔ مواد اولیه ایجاد شد."); }
      closeCategory(); await load();
    } catch (error:any) { setMessage(error.message || "ذخیرهٔ دستهٔ مواد اولیه انجام نشد."); }
    finally { setSavingCategory(false); }
  };
  const toggleActive = async (material:Material) => {
    try { await api<Material>(`/inventory-items/${material.id}/`, {method:"PATCH", body:JSON.stringify({is_active:!material.is_active})}); setMessage(`ماده اولیه ${material.is_active ? "غیرفعال" : "فعال"} شد.`); await load(); }
    catch (error:any) { setMessage(error.message || "تغییر وضعیت ماده اولیه انجام نشد."); }
  };
  const toggleCategory = async (category:MaterialCategory) => {
    try { await api<MaterialCategory>(`/ingredient-categories/${category.id}/`, {method:"PATCH", body:JSON.stringify({is_active:!category.is_active})}); setMessage(`دستهٔ مواد اولیه ${category.is_active ? "غیرفعال" : "فعال"} شد.`); await load(); }
    catch (error:any) { setMessage(error.message || "تغییر وضعیت دسته انجام نشد."); }
  };
  const deleteCategory = async (category:MaterialCategory) => {
    if (!confirm(`دستهٔ «${category.name}» حذف شود؟ حذف فقط زمانی ممکن است که هیچ ماده‌ای به آن متصل نباشد.`)) return;
    try { await api<void>(`/ingredient-categories/${category.id}/`, {method:"DELETE"}); setMessage("دستهٔ مواد اولیه حذف شد."); await load(); }
    catch (error:any) { setMessage(error.message || "حذف دسته انجام نشد."); }
  };

  const activeCount = branchMaterials.filter(material => material.is_active).length;
  const lowCount = branchMaterials.filter(material => material.low_stock).length;
  return <div className="space-y-5">
    <header className="flex flex-col gap-4 rounded-[22px] border border-[#eadfd3] bg-[#fffdf9] p-5 shadow-sm lg:flex-row lg:items-end lg:justify-between"><div><p className="mb-1 text-sm font-bold text-[#b9792d]">انبار و رسپی</p><h1 className="text-3xl font-black">مواد اولیه</h1><p className="mt-2 text-[#8d8178]">مواد، دسته‌بندی و وضعیت موجودی را بدون شلوغ‌شدن صفحه مدیریت کنید.</p></div><div className="flex flex-wrap items-end gap-2"><label className="text-sm font-bold">شعبهٔ فعال<select className="btn mr-2 min-w-44" value={selectedBranchId || ""} onChange={event => setSelectedBranchId(Number(event.target.value))} disabled={!branches.length}>{branches.map(branch => <option key={branch.id} value={branch.id}>{branch.name}</option>)}</select></label><button type="button" className="btn" onClick={() => { setEditingCategory(null); setCategoryName(""); setCategoryDialog(true); }} disabled={!selectedBranch}>دسته‌های مواد</button><button type="button" className="btn btn-primary" onClick={() => { setEditing(null); setForm(emptyForm); setMaterialDialog(true); }} disabled={!selectedBranch}>افزودن ماده اولیه</button></div></header>
    {message && <div role="status" className="card border-r-4 border-r-[#b9792d] p-4">{message}</div>}
    {!loading && !selectedBranch && <div className="card p-6">شعبه‌ای برای این کاربر تعریف نشده است.</div>}
    {selectedBranch && <><section className="grid gap-3 md:grid-cols-3"><div className="card p-4"><div className="text-sm text-[#8d8178]">کل مواد اولیه</div><b className="mt-1 block text-2xl">{branchMaterials.length.toLocaleString("fa-IR")}</b></div><div className="card p-4"><div className="text-sm text-[#8d8178]">مواد فعال</div><b className="mt-1 block text-2xl text-emerald-700">{activeCount.toLocaleString("fa-IR")}</b></div><div className="card p-4"><div className="text-sm text-[#8d8178]">نیازمند تأمین</div><b className="mt-1 block text-2xl text-red-700">{lowCount.toLocaleString("fa-IR")}</b></div></section><section className="card overflow-hidden"><div className="flex flex-col gap-2 border-b border-[#eadfd3] p-4 lg:flex-row"><input className="btn min-w-0 flex-1" placeholder="جست‌وجوی نام، دسته یا کد ماده" value={search} onChange={event => setSearch(event.target.value)}/><select className="btn" value={categoryFilter} onChange={event => setCategoryFilter(event.target.value)}><option value="all">همهٔ دسته‌ها</option>{branchCategories.map(category => <option key={category.id} value={category.id}>{category.name}</option>)}</select><Link className="btn text-center" href="/recipes">رفتن به رسپی‌ساز</Link><button type="button" className="btn btn-primary" onClick={() => { setEditing(null); setForm(emptyForm); setMaterialDialog(true); }}>افزودن ماده</button></div>{visibleMaterials.length ? <div className="overflow-x-auto"><table className="w-full min-w-[820px]"><thead className="bg-[#f7f0e8]"><tr><th className="p-3 text-right">نام</th><th className="text-right">دسته</th><th className="text-right">واحد</th><th className="text-right">موجودی</th><th className="text-right">حداقل</th><th className="text-right">هزینهٔ واحد</th><th className="text-right">وضعیت</th><th className="p-3 text-left">عملیات</th></tr></thead><tbody>{visibleMaterials.map(material => <tr className="border-t border-[#f0e8df]" key={material.id}><td className="p-3 font-bold">{material.name}<div className="mt-1 text-xs font-normal text-[#8d8178]">{material.item_code || "بدون کد"}</div></td><td>{material.material_category_name || material.category || "بدون دسته"}</td><td>{unitLabels[material.unit] || material.unit}</td><td>{Number(material.current_stock).toLocaleString("fa-IR")}</td><td>{Number(material.minimum_stock).toLocaleString("fa-IR")}</td><td>{Number(material.average_cost).toLocaleString("fa-IR")} ریال</td><td><span className={material.is_active ? material.low_stock ? "font-bold text-red-700" : "font-bold text-emerald-700" : "text-[#8d8178]"}>{material.is_active ? material.low_stock ? "نیازمند تأمین" : "فعال" : "غیرفعال"}</span></td><td className="p-3"><div className="flex justify-end gap-1"><button type="button" className="btn text-xs" onClick={() => openEdit(material)}>ویرایش</button><button type="button" className="btn text-xs" onClick={() => void toggleActive(material)}>{material.is_active ? "غیرفعال‌کردن" : "فعال‌کردن"}</button></div></td></tr>)}</tbody></table></div> : <div className="p-10 text-center"><b>{search || categoryFilter !== "all" ? "ماده‌ای با این مشخصات یافت نشد." : "هنوز ماده اولیه‌ای ثبت نشده است."}</b><p className="mt-2 text-sm text-[#8d8178]">با افزودن ماده اولیه، آن را در رسپی‌ساز انتخاب خواهید کرد.</p></div>}</section></>}
    <FormDialog open={materialDialog} onClose={closeMaterial} closeDisabled={saving} width="lg" title={editing ? `ویرایش «${editing.name}»` : "افزودن ماده اولیه"} description="موجودی و هزینه بر پایهٔ واحد مصرفی ثبت می‌شوند."><form className="space-y-4" onSubmit={save}><div className="grid gap-4 sm:grid-cols-2"><label className="text-sm font-bold">نام ماده اولیه<input autoFocus className="btn mt-1 w-full" placeholder="مثلاً شیر تازه" value={form.name} onChange={event => setForm({...form, name:event.target.value})}/></label><label className="text-sm font-bold">دستهٔ ماده اولیه<select className="btn mt-1 w-full" value={form.material_category} onChange={event => setForm({...form, material_category:event.target.value})}><option value="">بدون دسته‌بندی</option>{branchCategories.filter(category => category.is_active || category.id === Number(form.material_category)).map(category => <option key={category.id} value={category.id}>{category.name}{category.is_active ? "" : " (غیرفعال)"}</option>)}</select></label><label className="text-sm font-bold">واحد مصرف<select className="btn mt-1 w-full" value={form.unit} onChange={event => setForm({...form, unit:event.target.value})}>{Object.entries(unitLabels).map(([value,label]) => <option key={value} value={value}>{label}</option>)}</select></label><label className="text-sm font-bold">کد داخلی ماده<input className="btn mt-1 w-full" placeholder="مثلاً MILK-01" value={form.item_code} onChange={event => setForm({...form, item_code:event.target.value})}/></label><label className="text-sm font-bold">موجودی اولیه<input className="btn mt-1 w-full" inputMode="decimal" placeholder="مثلاً ۵۰۰۰" value={form.current_stock} onChange={event => setForm({...form, current_stock:event.target.value})}/></label><label className="text-sm font-bold">حداقل موجودی<input className="btn mt-1 w-full" inputMode="decimal" placeholder="مثلاً ۱۰۰۰" value={form.minimum_stock} onChange={event => setForm({...form, minimum_stock:event.target.value})}/></label><label className="text-sm font-bold">هزینهٔ هر واحد (ریال)<input className="btn mt-1 w-full" inputMode="decimal" placeholder="مثلاً ۲۵٬۰۰۰" value={form.average_cost} onChange={event => setForm({...form, average_cost:event.target.value})}/></label><label className="text-sm font-bold">ماندگاری (روز)<input className="btn mt-1 w-full" inputMode="numeric" placeholder="مثلاً ۷" value={form.shelf_life_days} onChange={event => setForm({...form, shelf_life_days:event.target.value})}/></label></div><label className="flex items-center gap-2 rounded-xl bg-[#f7f0e8] p-3 text-sm font-bold"><input type="checkbox" checked={form.lot_tracked} onChange={event => setForm({...form, lot_tracked:event.target.checked})}/> رهگیری سری ساخت و تاریخ انقضا برای این ماده فعال باشد</label><footer className="flex justify-end gap-2 border-t border-[#eadfd3] pt-4"><button type="button" className="btn" onClick={closeMaterial} disabled={saving}>انصراف</button><button className="btn btn-primary" disabled={saving}>{saving ? "در حال ذخیره…" : editing ? "ذخیرهٔ تغییرات" : "ثبت ماده اولیه"}</button></footer></form></FormDialog>
    <FormDialog open={categoryDialog} onClose={closeCategory} closeDisabled={savingCategory} title={editingCategory ? `ویرایش دستهٔ «${editingCategory.name}»` : "مدیریت دسته‌های مواد اولیه"} description="از دسته‌ها برای مرتب‌سازی و فیلتر مواد استفاده کنید."><form className="space-y-4" onSubmit={saveCategory}><label className="block text-sm font-bold">نام دسته<input autoFocus className="btn mt-1 w-full" placeholder="مثلاً لبنیات" value={categoryName} onChange={event => setCategoryName(event.target.value)} maxLength={80}/></label><footer className="flex justify-end gap-2"><button type="button" className="btn" onClick={closeCategory} disabled={savingCategory}>انصراف</button><button className="btn btn-primary" disabled={savingCategory || !categoryName.trim()}>{savingCategory ? "در حال ذخیره…" : editingCategory ? "ذخیرهٔ تغییرات" : "ثبت دسته"}</button></footer></form><div className="mt-5 border-t border-[#eadfd3] pt-4"><h3 className="font-black">دسته‌های ثبت‌شده</h3><div className="mt-3 space-y-2">{branchCategories.length ? branchCategories.map(category => <div key={category.id} className="flex items-center justify-between gap-2 rounded-xl border border-[#eadfd3] p-3"><span className={category.is_active ? "font-bold" : "text-[#8d8178] line-through"}>{category.name}</span><div className="flex flex-wrap gap-1"><button type="button" className="btn text-xs" onClick={() => openCategoryEdit(category)}>ویرایش</button><button type="button" className="btn text-xs" onClick={() => void toggleCategory(category)}>{category.is_active ? "غیرفعال‌کردن" : "فعال‌کردن"}</button><button type="button" className="btn text-xs text-red-700" onClick={() => void deleteCategory(category)}>حذف</button></div></div>) : <p className="text-sm text-[#8d8178]">هنوز دسته‌ای ثبت نشده است.</p>}</div></div></FormDialog>
  </div>;
}

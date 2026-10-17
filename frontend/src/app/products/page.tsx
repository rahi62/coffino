"use client";

import {FormEvent, useEffect, useMemo, useState} from "react";
import FormDialog from "@/components/form-dialog";
import {api} from "@/lib/api";

type Branch = {id:number; name:string};
type Category = {id:number; branch:number; name:string; sort_order:number; is_active:boolean};
type InventoryItem = {id:number; branch:number; name:string; current_stock:number|string};
type Station = {id:number; branch:number; name:string; code:string; is_active:boolean};
type Product = {id:number; branch:number; name:string; price:number|string; category:number|null; category_name:string|null; product_type:string; stock_item:number|null; preparation_station:number|null; station_name:string|null; is_available:boolean};
type ProductForm = {name:string; price:string; category:string; product_type:string; stock_item:string; preparation_station:string};

const branchStorageKey = "cafino_settings_branch";
const emptyProduct: ProductForm = {name:"", price:"", category:"", product_type:"PREPARED_ITEM", stock_item:"", preparation_station:""};
const productTypeLabels: Record<string,string> = {PREPARED_ITEM:"آماده‌سازی‌شونده", PACKAGED_ITEM:"بسته‌ای", RETAIL_ITEM:"فروشگاهی", WEIGHTED_ITEM:"وزنی"};

export default function Products() {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [stations, setStations] = useState<Station[]>([]);
  const [selectedBranchId, setSelectedBranchId] = useState<number|null>(null);
  const [productForm, setProductForm] = useState<ProductForm>(emptyProduct);
  const [categoryName, setCategoryName] = useState("");
  const [stationName, setStationName] = useState("");
  const [editingProduct, setEditingProduct] = useState<Product|null>(null);
  const [editingCategory, setEditingCategory] = useState<Category|null>(null);
  const [productDialog, setProductDialog] = useState(false);
  const [categoryDialog, setCategoryDialog] = useState(false);
  const [stationDialog, setStationDialog] = useState(false);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [savingProduct, setSavingProduct] = useState(false);
  const [savingCategory, setSavingCategory] = useState(false);
  const [savingStation, setSavingStation] = useState(false);

  const load = async () => {
    setLoading(true);
    const [productsResult,categoriesResult,branchesResult,inventoryResult,stationsResult]=await Promise.allSettled([
      api<Product[]>("/products/"),api<Category[]>("/categories/"),api<Branch[]>("/branches/"),
      api<InventoryItem[]>("/inventory-items/"),api<Station[]>("/stations/"),
    ]);
    if(productsResult.status==="fulfilled")setProducts(productsResult.value);
    if(categoriesResult.status==="fulfilled")setCategories(categoriesResult.value);
    if(branchesResult.status==="fulfilled"){
      const nextBranches=branchesResult.value;
      setBranches(nextBranches);
      setSelectedBranchId(current=>{
        if(current&&nextBranches.some(branch=>branch.id===current))return current;
        const stored=Number(localStorage.getItem(branchStorageKey)||0);
        return nextBranches.some(branch=>branch.id===stored)?stored:nextBranches[0]?.id||null;
      });
    }
    if(inventoryResult.status==="fulfilled")setInventory(inventoryResult.value);
    if(stationsResult.status==="fulfilled")setStations(stationsResult.value);
    const failures=[productsResult,categoriesResult,branchesResult,inventoryResult,stationsResult].filter(result=>result.status==="rejected");
    if(failures.length)setMessage("بخشی از اطلاعات دریافت نشد. دسته‌بندی‌های دریافت‌شده و سایر اطلاعات موفق همچنان نمایش داده می‌شوند.");
    setLoading(false);
  };
  useEffect(() => { void load(); }, []);
  useEffect(() => { if (selectedBranchId) localStorage.setItem(branchStorageKey, String(selectedBranchId)); }, [selectedBranchId]);

  const selectedBranch = branches.find(branch => branch.id === selectedBranchId) || null;
  const branchCategories = useMemo(() => categories.filter(category => category.branch === selectedBranchId), [categories, selectedBranchId]);
  const branchInventory = useMemo(() => inventory.filter(item => item.branch === selectedBranchId), [inventory, selectedBranchId]);
  const branchStations = useMemo(() => stations.filter(station => station.branch === selectedBranchId), [stations, selectedBranchId]);
  const branchProducts = useMemo(() => products.filter(product => product.branch === selectedBranchId), [products, selectedBranchId]);

  const closeProductDialog = () => { setProductDialog(false); setEditingProduct(null); setProductForm(emptyProduct); };
  const closeCategoryDialog = () => { setCategoryDialog(false); setEditingCategory(null); setCategoryName(""); };
  const openNewProduct = () => { setEditingProduct(null); setProductForm(emptyProduct); setProductDialog(true); };
  const openProductEdit = (product:Product) => {
    setEditingProduct(product);
    setProductForm({name:product.name, price:String(product.price), category:product.category ? String(product.category) : "", product_type:product.product_type, stock_item:product.stock_item ? String(product.stock_item) : "", preparation_station:product.preparation_station ? String(product.preparation_station) : ""});
    setProductDialog(true);
  };
  const openCategoryEdit = (category:Category) => { setEditingCategory(category); setCategoryName(category.name); setCategoryDialog(true); };

  const createStation = async (event:FormEvent) => {
    event.preventDefault();
    if (!selectedBranchId || !stationName.trim()) return;
    setSavingStation(true); setMessage("");
    try {
      const station = await api<Station>("/stations/", {method:"POST", body:JSON.stringify({branch:selectedBranchId, name:stationName.trim(), code:`ST-${Date.now()}`, is_active:true})});
      setProductForm(current => ({...current, preparation_station:String(station.id)}));
      setStationName(""); setStationDialog(false); setMessage("ایستگاه آماده‌سازی ایجاد و برای محصول انتخاب شد."); await load();
    } catch (error:any) { setMessage(error.message || "ایجاد ایستگاه آماده‌سازی انجام نشد."); }
    finally { setSavingStation(false); }
  };

  const saveCategory = async (event:FormEvent) => {
    event.preventDefault();
    if(!selectedBranchId||!categoryName.trim()||savingCategory)return;
    const targetBranch=selectedBranchId;
    setSavingCategory(true);setMessage("");
    try{
      let saved:Category;
      if(editingCategory){
        saved=await api<Category>(`/categories/${editingCategory.id}/`,{method:"PATCH",body:JSON.stringify({name:categoryName.trim()})});
        setCategories(current=>current.map(category=>category.id===saved.id?saved:category));
        setMessage(`دسته‌بندی «${saved.name}» ویرایش شد (شناسه ${saved.id.toLocaleString("fa-IR")}).`);
      }else{
        saved=await api<Category>("/categories/",{method:"POST",body:JSON.stringify({branch:targetBranch,name:categoryName.trim(),sort_order:branchCategories.length,is_active:true})});
        setCategories(current=>current.some(category=>category.id===saved.id)?current.map(category=>category.id===saved.id?saved:category):[...current,saved]);
        setProductForm(current=>({...current,category:String(saved.id)}));
        setMessage(`دسته‌بندی «${saved.name}» ایجاد شد (شناسه ${saved.id.toLocaleString("fa-IR")}).`);
      }
      closeCategoryDialog();
      // Saving succeeded. Do not report a save failure if unrelated reads fail.
    }catch(error:any){setMessage(error.message||"ذخیره دسته‌بندی انجام نشد.");}
    finally{setSavingCategory(false);}
  };
  const setCategoryActive = async (category:Category) => {
    try { await api<Category>(`/categories/${category.id}/`, {method:"PATCH", body:JSON.stringify({is_active:!category.is_active})}); setMessage(`دسته‌بندی ${category.is_active ? "غیرفعال" : "فعال"} شد.`); await load(); }
    catch (error:any) { setMessage(error.message || "تغییر وضعیت دسته‌بندی انجام نشد."); }
  };
  const deleteCategory = async (category:Category) => {
    if (!confirm(`دسته‌بندی «${category.name}» حذف شود؟ این کار فقط در صورت نداشتن محصول و قانون تخفیف وابسته انجام می‌شود.`)) return;
    try { await api<void>(`/categories/${category.id}/`, {method:"DELETE"}); setMessage("دسته‌بندی حذف شد."); await load(); }
    catch (error:any) { setMessage(error.message || "حذف دسته‌بندی انجام نشد."); }
  };

  const saveProduct = async (event:FormEvent) => {
    event.preventDefault();
    if (!selectedBranchId) return;
    if (!productForm.name.trim() || !productForm.price.trim()) { setMessage("نام و قیمت محصول را وارد کنید."); return; }
    setSavingProduct(true); setMessage("");
    const payload = {name:productForm.name.trim(), price:Number(productForm.price), category:productForm.category ? Number(productForm.category) : null, product_type:productForm.product_type, stock_item:productForm.stock_item ? Number(productForm.stock_item) : null, preparation_station:productForm.preparation_station ? Number(productForm.preparation_station) : null};
    try {
      if (editingProduct) { await api<Product>(`/products/${editingProduct.id}/`, {method:"PATCH", body:JSON.stringify(payload)}); setMessage("محصول ویرایش شد."); }
      else { await api<Product>("/products/", {method:"POST", body:JSON.stringify({...payload, branch:selectedBranchId, is_available:true})}); setMessage("محصول جدید با موفقیت ثبت شد."); }
      closeProductDialog(); await load();
    } catch (error:any) { setMessage(error.message || "ذخیرهٔ محصول انجام نشد."); }
    finally { setSavingProduct(false); }
  };
  const setProductActive = async (product:Product) => {
    try { await api<Product>(`/products/${product.id}/`, {method:"PATCH", body:JSON.stringify({is_available:!product.is_available})}); setMessage(`محصول ${product.is_available ? "غیرفعال" : "فعال"} شد.`); await load(); }
    catch (error:any) { setMessage(error.message || "تغییر وضعیت محصول انجام نشد."); }
  };
  const deleteProduct = async (product:Product) => {
    if (!confirm(`محصول «${product.name}» حذف شود؟ اگر در سفارش یا قانون تخفیف استفاده شده باشد، حذف نمی‌شود.`)) return;
    try { await api<void>(`/products/${product.id}/`, {method:"DELETE"}); setMessage("محصول حذف شد."); await load(); }
    catch (error:any) { setMessage(error.message || "حذف محصول انجام نشد."); }
  };

  return <div className="space-y-5">
    <header className="flex flex-col gap-4 rounded-[22px] border border-[#eadfd3] bg-[#fffdf9] p-5 shadow-sm lg:flex-row lg:items-end lg:justify-between">
      <div><p className="mb-1 text-sm font-bold text-[#b9792d]">منو و آماده‌سازی</p><h1 className="text-3xl font-black">مدیریت محصولات</h1><p className="mt-2 text-[#8d8178]">منوی هر شعبه، دسته‌بندی و مسیر ارسال سفارش به آشپزخانه را در یک‌جا کنترل کنید.</p></div>
      <div className="flex flex-wrap items-end gap-2"><label className="text-sm font-bold">شعبهٔ فعال<select className="btn mr-2 min-w-44" value={selectedBranchId || ""} onChange={event => setSelectedBranchId(Number(event.target.value))} disabled={!branches.length}>{branches.map(branch => <option key={branch.id} value={branch.id}>{branch.name}</option>)}</select></label><button type="button" className="btn" onClick={() => { setEditingCategory(null); setCategoryName(""); setCategoryDialog(true); }} disabled={!selectedBranch}>مدیریت دسته‌ها</button><button type="button" className="btn btn-primary" onClick={openNewProduct} disabled={!selectedBranch}>افزودن محصول</button></div>
    </header>
    {message && <div role="status" className="card border-r-4 border-r-[#b9792d] p-4">{message}</div>}
    {!loading && !selectedBranch && <div className="card p-6"><b>شعبه‌ای برای این کاربر تعریف نشده است.</b><p className="mt-2 text-sm text-[#8d8178]">ابتدا یک شعبه ایجاد کنید یا دسترسی کاربر را بررسی کنید.</p></div>}
    {selectedBranch && <>
      <section className="grid gap-3 sm:grid-cols-3"><div className="card p-4"><div className="text-sm text-[#8d8178]">محصول‌های ثبت‌شده</div><b className="mt-1 block text-2xl">{branchProducts.length.toLocaleString("fa-IR")}</b></div><div className="card p-4"><div className="text-sm text-[#8d8178]">محصول‌های فعال</div><b className="mt-1 block text-2xl text-emerald-700">{branchProducts.filter(product => product.is_available).length.toLocaleString("fa-IR")}</b></div><div className="card p-4"><div className="text-sm text-[#8d8178]">متصل به آماده‌سازی</div><b className="mt-1 block text-2xl text-[#b9792d]">{branchProducts.filter(product => product.preparation_station).length.toLocaleString("fa-IR")}</b></div></section>
      <section className="card overflow-hidden"><div className="flex flex-col gap-2 border-b border-[#eadfd3] p-4 sm:flex-row sm:items-center sm:justify-between"><div><h2 className="font-black">فهرست منوی {selectedBranch.name}</h2><p className="mt-1 text-sm text-[#8d8178]">ویرایش و وضعیت‌گذاری بدون ترک فهرست انجام می‌شود.</p></div><button type="button" className="btn btn-primary self-start" onClick={openNewProduct}>افزودن محصول</button></div><div className="overflow-x-auto"><table className="w-full min-w-[900px]"><thead className="bg-[#f7f0e8]"><tr><th className="p-3 text-right">محصول</th><th className="text-right">نوع</th><th className="text-right">دسته‌بندی</th><th className="text-right">قیمت</th><th className="text-right">ایستگاه آماده‌سازی</th><th className="text-right">وضعیت</th><th className="p-3 text-left">عملیات</th></tr></thead><tbody>{branchProducts.length ? branchProducts.map(product => <tr className="border-t border-[#f0e8df]" key={product.id}><td className="p-3 font-bold">{product.name}</td><td>{productTypeLabels[product.product_type] || product.product_type}</td><td>{product.category_name || "بدون دسته"}</td><td>{Number(product.price).toLocaleString("fa-IR")} ریال</td><td className={product.preparation_station ? "" : "text-[#8d8178]"}>{product.station_name || "ارسال نمی‌شود"}</td><td><span className={product.is_available ? "badge bg-emerald-100 text-emerald-800" : "badge text-[#8d8178]"}>{product.is_available ? "فعال" : "غیرفعال"}</span></td><td className="p-3"><div className="flex justify-end gap-1"><button type="button" className="btn text-xs" onClick={() => openProductEdit(product)}>ویرایش</button><button type="button" className="btn text-xs" onClick={() => void setProductActive(product)}>{product.is_available ? "غیرفعال‌کردن" : "فعال‌کردن"}</button><button type="button" className="btn text-xs text-red-700" onClick={() => void deleteProduct(product)}>حذف</button></div></td></tr>) : <tr><td colSpan={7} className="p-10 text-center"><b>هنوز محصولی برای این شعبه ثبت نشده است.</b><p className="mt-2 text-sm text-[#8d8178]">با افزودن نخستین محصول، منوی فروش و آماده‌سازی آن فعال می‌شود.</p></td></tr>}</tbody></table></div></section>
    </>}

    <FormDialog open={productDialog} onClose={closeProductDialog} closeDisabled={savingProduct} width="lg" title={editingProduct ? `ویرایش «${editingProduct.name}»` : "افزودن محصول"} description="محصول آماده‌سازی‌شونده را به ایستگاه وصل کنید تا در آشپزخانه نمایش داده شود.">
      <form className="space-y-4" onSubmit={saveProduct}><div className="grid gap-4 sm:grid-cols-2"><label className="text-sm font-bold">نام محصول<input autoFocus className="btn mt-1 w-full" placeholder="مثلاً لاته" value={productForm.name} onChange={event => setProductForm({...productForm, name:event.target.value})}/></label><label className="text-sm font-bold">قیمت فروش (ریال)<input className="btn mt-1 w-full" inputMode="numeric" placeholder="مثلاً ۲۵۰٬۰۰۰" value={productForm.price} onChange={event => setProductForm({...productForm, price:event.target.value})}/></label><label className="text-sm font-bold">دسته‌بندی<select className="btn mt-1 w-full" value={productForm.category} onChange={event => setProductForm({...productForm, category:event.target.value})}><option value="">بدون دسته‌بندی</option>{branchCategories.filter(category => category.is_active || category.id === Number(productForm.category)).map(category => <option key={category.id} value={category.id}>{category.name}{category.is_active ? "" : " (غیرفعال)"}</option>)}</select></label><label className="text-sm font-bold">نوع محصول<select className="btn mt-1 w-full" value={productForm.product_type} onChange={event => setProductForm({...productForm, product_type:event.target.value})}>{Object.entries(productTypeLabels).map(([value,label]) => <option key={value} value={value}>{label}</option>)}</select></label></div><label className="block text-sm font-bold">اتصال به قلم انبار<select className="btn mt-1 w-full" value={productForm.stock_item} onChange={event => setProductForm({...productForm, stock_item:event.target.value})}><option value="">بدون اتصال به قلم انبار</option>{branchInventory.map(item => <option key={item.id} value={item.id}>{item.name} — موجودی {Number(item.current_stock).toLocaleString("fa-IR")}</option>)}</select></label><div className="rounded-2xl border border-[#eadfd3] bg-[#fdf9f4] p-4"><div className="flex flex-wrap items-center justify-between gap-2"><label className="min-w-56 flex-1 text-sm font-bold">ایستگاه آماده‌سازی<select className="btn mt-1 w-full" value={productForm.preparation_station} onChange={event => setProductForm({...productForm, preparation_station:event.target.value})}><option value="">بدون ارسال به آشپزخانه</option>{branchStations.filter(station => station.is_active || station.id === Number(productForm.preparation_station)).map(station => <option key={station.id} value={station.id}>{station.name}{station.is_active ? "" : " (غیرفعال)"}</option>)}</select></label><button type="button" className="btn mt-5" onClick={() => setStationDialog(true)}>ایجاد ایستگاه</button></div><p className="mt-2 text-xs text-[#8d8178]">این اتصال مستقل از وضعیت پرداخت است و سفارش را برای آماده‌سازی ارسال می‌کند.</p></div><footer className="flex flex-wrap justify-end gap-2 border-t border-[#eadfd3] pt-4"><button type="button" className="btn" onClick={closeProductDialog} disabled={savingProduct}>انصراف</button><button className="btn btn-primary" disabled={savingProduct}>{savingProduct ? "در حال ذخیره…" : editingProduct ? "ذخیرهٔ تغییرات" : "ثبت محصول"}</button></footer></form>
    </FormDialog>
    <FormDialog open={categoryDialog} onClose={closeCategoryDialog} closeDisabled={savingCategory} title={editingCategory ? `ویرایش دستهٔ «${editingCategory.name}»` : "مدیریت دسته‌بندی‌ها"} description={`دسته‌ها فقط در شعبه «${selectedBranch?.name||"انتخاب‌نشده"}» قابل استفاده‌اند.`}>
      <form className="space-y-4" onSubmit={saveCategory}><label className="block text-sm font-bold">نام دسته‌بندی<input autoFocus className="btn mt-1 w-full" placeholder="مثلاً نوشیدنی گرم" value={categoryName} onChange={event => setCategoryName(event.target.value)} maxLength={120}/></label><footer className="flex justify-end gap-2"><button type="button" className="btn" onClick={closeCategoryDialog} disabled={savingCategory}>انصراف</button><button className="btn btn-primary" disabled={savingCategory || !categoryName.trim()}>{savingCategory ? "در حال ذخیره…" : editingCategory ? "ذخیرهٔ تغییرات" : "ثبت دسته‌بندی"}</button></footer></form><div className="mt-5 border-t border-[#eadfd3] pt-4"><h3 className="font-black">دسته‌های ثبت‌شده</h3><div className="mt-3 space-y-2">{branchCategories.length ? branchCategories.map(category => <div key={category.id} className="flex items-center justify-between gap-2 rounded-xl border border-[#eadfd3] p-3"><span className={category.is_active ? "font-bold" : "text-[#8d8178] line-through"}>{category.name}</span><div className="flex flex-wrap gap-1"><button type="button" className="btn text-xs" onClick={() => openCategoryEdit(category)}>ویرایش</button><button type="button" className="btn text-xs" onClick={() => void setCategoryActive(category)}>{category.is_active ? "غیرفعال‌کردن" : "فعال‌کردن"}</button><button type="button" className="btn text-xs text-red-700" onClick={() => void deleteCategory(category)}>حذف</button></div></div>) : <p className="text-sm text-[#8d8178]">هنوز دسته‌بندی‌ای ثبت نشده است.</p>}</div></div>
    </FormDialog>
    <FormDialog open={stationDialog} onClose={() => { setStationDialog(false); setStationName(""); }} closeDisabled={savingStation} width="sm" title="ایجاد ایستگاه آماده‌سازی" description="مثلاً بار گرم، آشپزخانه یا دسر."><form className="space-y-4" onSubmit={createStation}><label className="block text-sm font-bold">نام ایستگاه<input autoFocus className="btn mt-1 w-full" placeholder="مثلاً بار گرم" value={stationName} onChange={event => setStationName(event.target.value)} maxLength={120}/></label><footer className="flex justify-end gap-2"><button type="button" className="btn" onClick={() => setStationDialog(false)} disabled={savingStation}>انصراف</button><button className="btn btn-primary" disabled={savingStation || !stationName.trim()}>{savingStation ? "در حال ایجاد…" : "ایجاد و انتخاب"}</button></footer></form></FormDialog>
  </div>;
}

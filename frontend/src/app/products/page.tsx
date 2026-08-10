"use client";

import {FormEvent,useEffect,useMemo,useState} from "react";
import {api} from "@/lib/api";

type Branch={id:number;name:string};
type Category={id:number;branch:number;name:string;sort_order:number;is_active:boolean};
type InventoryItem={id:number;branch:number;name:string;current_stock:number|string};
type Station={id:number;branch:number;name:string;code:string;is_active:boolean};
type Product={id:number;branch:number;name:string;price:number|string;category:number|null;category_name:string|null;product_type:string;stock_item:number|null;preparation_station:number|null;station_name:string|null;is_available:boolean};
type ProductForm={name:string;price:string;category:string;product_type:string;stock_item:string;preparation_station:string};

const branchStorageKey="cafino_settings_branch";
const emptyProduct:ProductForm={name:"",price:"",category:"",product_type:"PREPARED_ITEM",stock_item:"",preparation_station:""};
const productTypeLabels:Record<string,string>={PREPARED_ITEM:"آماده‌سازی‌شونده",PACKAGED_ITEM:"بسته‌ای",RETAIL_ITEM:"فروشگاهی",WEIGHTED_ITEM:"وزنی"};

export default function Products(){
 const [products,setProducts]=useState<Product[]>([]),[categories,setCategories]=useState<Category[]>([]),[branches,setBranches]=useState<Branch[]>([]),[inventory,setInventory]=useState<InventoryItem[]>([]),[stations,setStations]=useState<Station[]>([]);
 const [selectedBranchId,setSelectedBranchId]=useState<number|null>(null),[productForm,setProductForm]=useState<ProductForm>(emptyProduct),[categoryName,setCategoryName]=useState("");
 const [editingProduct,setEditingProduct]=useState<Product|null>(null),[editingCategory,setEditingCategory]=useState<Category|null>(null);
 const [message,setMessage]=useState(""),[loading,setLoading]=useState(true),[savingProduct,setSavingProduct]=useState(false),[savingCategory,setSavingCategory]=useState(false),[stationName,setStationName]=useState(""),[savingStation,setSavingStation]=useState(false);

 const load=async()=>{
  setLoading(true);
  try{
   const [nextProducts,nextCategories,nextBranches,nextInventory,nextStations]=await Promise.all([api<Product[]>("/products/"),api<Category[]>("/categories/"),api<Branch[]>("/branches/"),api<InventoryItem[]>("/inventory-items/"),api<Station[]>("/stations/")]);
   setProducts(nextProducts);setCategories(nextCategories);setBranches(nextBranches);setInventory(nextInventory);setStations(nextStations);
   setSelectedBranchId(current=>{if(current&&nextBranches.some(branch=>branch.id===current))return current;const stored=Number(localStorage.getItem(branchStorageKey)||0);return nextBranches.some(branch=>branch.id===stored)?stored:nextBranches[0]?.id||null});
  }catch(error:any){setMessage(error.message||"دریافت اطلاعات محصولات انجام نشد.")}
  finally{setLoading(false)}
 };
 useEffect(()=>{void load()},[]);
 useEffect(()=>{if(selectedBranchId)localStorage.setItem(branchStorageKey,String(selectedBranchId))},[selectedBranchId]);

 const selectedBranch=branches.find(branch=>branch.id===selectedBranchId)||null;
 const branchCategories=useMemo(()=>categories.filter(category=>category.branch===selectedBranchId),[categories,selectedBranchId]);
 const branchInventory=useMemo(()=>inventory.filter(item=>item.branch===selectedBranchId),[inventory,selectedBranchId]);
 const branchStations=useMemo(()=>stations.filter(station=>station.branch===selectedBranchId),[stations,selectedBranchId]);
 const branchProducts=useMemo(()=>products.filter(product=>product.branch===selectedBranchId),[products,selectedBranchId]);
 const resetProduct=()=>{setProductForm(emptyProduct);setEditingProduct(null)};
 const resetCategory=()=>{setCategoryName("");setEditingCategory(null)};

 const createStation=async()=>{
  if(!selectedBranchId||!stationName.trim())return;
  setSavingStation(true);setMessage("");
  try{const station=await api<Station>("/stations/",{method:"POST",body:JSON.stringify({branch:selectedBranchId,name:stationName.trim(),code:`ST-${Date.now()}`,is_active:true})});setStationName("");setProductForm(current=>({...current,preparation_station:String(station.id)}));setMessage("ایستگاه آماده‌سازی ایجاد و برای محصول انتخاب شد.");await load()}catch(error:any){setMessage(error.message||"ایجاد ایستگاه آماده‌سازی انجام نشد.")}finally{setSavingStation(false)}
 };

 const saveCategory=async(event:FormEvent)=>{
  event.preventDefault();if(!selectedBranchId||!categoryName.trim())return;
  setSavingCategory(true);setMessage("");
  try{
   if(editingCategory){await api<Category>(`/categories/${editingCategory.id}/`,{method:"PATCH",body:JSON.stringify({name:categoryName.trim()})});setMessage("دسته‌بندی ویرایش شد.")}
   else {const category=await api<Category>("/categories/",{method:"POST",body:JSON.stringify({branch:selectedBranchId,name:categoryName.trim(),sort_order:branchCategories.length,is_active:true})});setProductForm(current=>({...current,category:String(category.id)}));setMessage("دسته‌بندی جدید ایجاد و برای محصول انتخاب شد.")}
   resetCategory();await load();
  }catch(error:any){setMessage(error.message||"ذخیرهٔ دسته‌بندی انجام نشد.")}
  finally{setSavingCategory(false)}
 };

 const setCategoryActive=async(category:Category)=>{
  try{await api<Category>(`/categories/${category.id}/`,{method:"PATCH",body:JSON.stringify({is_active:!category.is_active})});setMessage(`دسته‌بندی ${category.is_active?"غیرفعال":"فعال"} شد.`);await load()}catch(error:any){setMessage(error.message||"تغییر وضعیت دسته‌بندی انجام نشد.")}
 };
 const deleteCategory=async(category:Category)=>{
  if(!confirm(`دسته‌بندی «${category.name}» حذف شود؟ این کار فقط در صورت نداشتن محصول و قانون تخفیف وابسته انجام می‌شود.`))return;
  try{await api<void>(`/categories/${category.id}/`,{method:"DELETE"});if(editingCategory?.id===category.id)resetCategory();setMessage("دسته‌بندی حذف شد.");await load()}catch(error:any){setMessage(error.message||"حذف دسته‌بندی انجام نشد.")}
 };

 const saveProduct=async(event:FormEvent)=>{
  event.preventDefault();if(!selectedBranchId)return;
  if(!productForm.name.trim()||!productForm.price.trim()){setMessage("نام و قیمت محصول را وارد کنید.");return}
  setSavingProduct(true);setMessage("");
  const payload={name:productForm.name.trim(),price:Number(productForm.price),category:productForm.category?Number(productForm.category):null,product_type:productForm.product_type,stock_item:productForm.stock_item?Number(productForm.stock_item):null,preparation_station:productForm.preparation_station?Number(productForm.preparation_station):null};
  try{
   if(editingProduct){await api<Product>(`/products/${editingProduct.id}/`,{method:"PATCH",body:JSON.stringify(payload)});setMessage("محصول ویرایش شد.")}
   else {await api<Product>("/products/",{method:"POST",body:JSON.stringify({...payload,branch:selectedBranchId,is_available:true})});setMessage("محصول جدید با موفقیت ثبت شد.")}
   resetProduct();await load();
  }catch(error:any){setMessage(error.message||"ذخیرهٔ محصول انجام نشد.")}
  finally{setSavingProduct(false)}
 };

 const setProductActive=async(product:Product)=>{
  try{await api<Product>(`/products/${product.id}/`,{method:"PATCH",body:JSON.stringify({is_available:!product.is_available})});setMessage(`محصول ${product.is_available?"غیرفعال":"فعال"} شد.`);await load()}catch(error:any){setMessage(error.message||"تغییر وضعیت محصول انجام نشد.")}
 };
 const deleteProduct=async(product:Product)=>{
  if(!confirm(`محصول «${product.name}» حذف شود؟ اگر در سفارش یا قانون تخفیف استفاده شده باشد، حذف نمی‌شود.`))return;
  try{await api<void>(`/products/${product.id}/`,{method:"DELETE"});if(editingProduct?.id===product.id)resetProduct();setMessage("محصول حذف شد.");await load()}catch(error:any){setMessage(error.message||"حذف محصول انجام نشد.")}
 };
 const startProductEdit=(product:Product)=>{setEditingProduct(product);setProductForm({name:product.name,price:String(product.price),category:product.category?String(product.category):"",product_type:product.product_type,stock_item:product.stock_item?String(product.stock_item):"",preparation_station:product.preparation_station?String(product.preparation_station):""});setMessage("")};
 const startCategoryEdit=(category:Category)=>{setEditingCategory(category);setCategoryName(category.name);setMessage("")};

 return <div className="space-y-5">
  <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between"><div><h1 className="text-3xl font-black mb-2">مدیریت محصولات</h1><p className="text-[#8d8178]">محصولات و دسته‌بندی‌های هر شعبه جداگانه مدیریت می‌شوند.</p></div><label className="text-sm font-bold">شعبهٔ فعال<select className="btn mr-2 min-w-48" value={selectedBranchId||""} onChange={event=>{setSelectedBranchId(Number(event.target.value));resetProduct();resetCategory()}} disabled={!branches.length}>{branches.map(branch=><option key={branch.id} value={branch.id}>{branch.name}</option>)}</select></label></div>
  {message&&<div role="status" className="card p-3">{message}</div>}
  {!loading&&!selectedBranch&&<div className="card p-6"><b>شعبه‌ای برای این کاربر تعریف نشده است.</b><p className="mt-2 text-sm text-[#8d8178]">ابتدا یک شعبه ایجاد کنید یا دسترسی کاربر را بررسی کنید.</p></div>}
  {selectedBranch&&<>
   <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_390px]">
    <form className="card p-5 space-y-3" onSubmit={saveProduct}><div className="flex items-start justify-between gap-3"><div><h2 className="text-lg font-black">{editingProduct?`ویرایش محصول «${editingProduct.name}»`:`افزودن محصول برای ${selectedBranch.name}`}</h2><p className="mt-1 text-sm text-[#8d8178]">محصول آماده‌سازی‌شونده را به ایستگاه متصل کنید تا سفارش آن، حتی در حالت پرداخت در پایان سرویس، در آشپزخانه نمایش داده شود.</p></div>{editingProduct&&<button type="button" className="btn" onClick={resetProduct}>انصراف</button>}</div><div className="grid gap-3 md:grid-cols-2"><input className="btn w-full" placeholder="نام محصول" value={productForm.name} onChange={event=>setProductForm({...productForm,name:event.target.value})}/><input className="btn w-full" inputMode="numeric" placeholder="قیمت به ریال" value={productForm.price} onChange={event=>setProductForm({...productForm,price:event.target.value})}/></div><div className="grid gap-3 md:grid-cols-2"><select className="btn w-full" value={productForm.category} onChange={event=>setProductForm({...productForm,category:event.target.value})}><option value="">بدون دسته‌بندی</option>{branchCategories.filter(category=>category.is_active||category.id===Number(productForm.category)).map(category=><option key={category.id} value={category.id}>{category.name}{category.is_active?"":" (غیرفعال)"}</option>)}</select><select className="btn w-full" value={productForm.product_type} onChange={event=>setProductForm({...productForm,product_type:event.target.value})}><option value="PREPARED_ITEM">آماده‌سازی‌شونده</option><option value="PACKAGED_ITEM">بسته‌ای</option><option value="RETAIL_ITEM">فروشگاهی</option><option value="WEIGHTED_ITEM">وزنی</option></select></div><select className="btn w-full" value={productForm.stock_item} onChange={event=>setProductForm({...productForm,stock_item:event.target.value})}><option value="">بدون اتصال به قلم انبار</option>{branchInventory.map(item=><option key={item.id} value={item.id}>{item.name} — موجودی {Number(item.current_stock).toLocaleString("fa-IR")}</option>)}</select><div className="space-y-2 rounded-xl border border-[#e9dfd3] p-3"><label className="block text-sm font-bold">ایستگاه آماده‌سازی<select className="btn mt-1 w-full" value={productForm.preparation_station} onChange={event=>setProductForm({...productForm,preparation_station:event.target.value})}><option value="">بدون ارسال به آشپزخانه</option>{branchStations.filter(station=>station.is_active||station.id===Number(productForm.preparation_station)).map(station=><option key={station.id} value={station.id}>{station.name}{station.is_active?"":" (غیرفعال)"}</option>)}</select></label><div className="flex gap-2"><input className="btn min-w-0 flex-1" placeholder="نام ایستگاه جدید؛ مثلاً بار گرم" value={stationName} onChange={event=>setStationName(event.target.value)} maxLength={120}/><button type="button" className="btn" onClick={()=>void createStation()} disabled={savingStation||!stationName.trim()}>{savingStation?"در حال ایجاد…":"ایجاد ایستگاه"}</button></div></div><button className="btn btn-primary" disabled={savingProduct}>{savingProduct?"در حال ذخیره…":editingProduct?"ذخیرهٔ تغییرات":"افزودن محصول"}</button></form>
    <form className="card p-5 space-y-3" onSubmit={saveCategory}><div className="flex items-start justify-between gap-3"><div><h2 className="text-lg font-black">{editingCategory?`ویرایش دستهٔ «${editingCategory.name}»`:`دسته‌بندی‌های ${selectedBranch.name}`}</h2><p className="mt-1 text-sm text-[#8d8178]">دستهٔ جدید فقط برای همین شعبه ایجاد می‌شود.</p></div>{editingCategory&&<button type="button" className="btn" onClick={resetCategory}>انصراف</button>}</div><label className="block text-sm font-bold" htmlFor="category-name">نام دسته‌بندی</label><input id="category-name" className="btn w-full" placeholder="مثلاً نوشیدنی گرم" value={categoryName} onChange={event=>setCategoryName(event.target.value)} maxLength={120}/><button className="btn btn-primary w-full" disabled={savingCategory||!categoryName.trim()}>{savingCategory?"در حال ذخیره…":editingCategory?"ذخیرهٔ تغییرات":"ایجاد دسته‌بندی"}</button><div className="border-t pt-3"><div className="mb-2 text-sm font-bold">دسته‌بندی‌های ثبت‌شده</div>{branchCategories.length?<div className="space-y-2">{branchCategories.map(category=><div key={category.id} className="flex items-center justify-between gap-2 rounded-xl border p-2"><span className={category.is_active?"font-bold":"text-[#8d8178] line-through"}>{category.name}</span><div className="flex flex-wrap justify-end gap-1"><button type="button" className="btn text-xs" onClick={()=>startCategoryEdit(category)}>ویرایش</button><button type="button" className="btn text-xs" onClick={()=>void setCategoryActive(category)}>{category.is_active?"غیرفعال‌کردن":"فعال‌کردن"}</button><button type="button" className="btn text-xs text-red-700" onClick={()=>void deleteCategory(category)}>حذف</button></div></div>)}</div>:<p className="text-sm text-[#8d8178]">هنوز دسته‌بندی‌ای برای این شعبه ندارید.</p>}</div></form>
   </section>
   <section className="card overflow-x-auto"><table className="w-full min-w-[980px]"><thead><tr><th className="p-3 text-right">محصول</th><th className="text-right">نوع</th><th className="text-right">دسته‌بندی</th><th className="text-right">قیمت</th><th className="text-right">ایستگاه آماده‌سازی</th><th className="text-right">قلم انبار</th><th className="text-right">وضعیت</th><th className="p-3 text-left">عملیات</th></tr></thead><tbody>{branchProducts.length?branchProducts.map(product=><tr className="border-t" key={product.id}><td className="p-3 font-bold">{product.name}</td><td>{productTypeLabels[product.product_type]||product.product_type}</td><td>{product.category_name||"—"}</td><td>{Number(product.price).toLocaleString("fa-IR")} ریال</td><td className={product.preparation_station?"":"text-amber-700"}>{product.station_name||"بدون ارسال به آشپزخانه"}</td><td>{product.stock_item?"متصل است":"—"}</td><td><span className={product.is_available?"badge":"badge opacity-60"}>{product.is_available?"فعال":"غیرفعال"}</span></td><td className="p-3"><div className="flex justify-end gap-1"><button type="button" className="btn text-xs" onClick={()=>startProductEdit(product)}>ویرایش</button><button type="button" className="btn text-xs" onClick={()=>void setProductActive(product)}>{product.is_available?"غیرفعال‌کردن":"فعال‌کردن"}</button><button type="button" className="btn text-xs text-red-700" onClick={()=>void deleteProduct(product)}>حذف</button></div></td></tr>):<tr><td colSpan={8} className="p-8 text-center text-[#8d8178]">هنوز محصولی برای این شعبه ثبت نشده است.</td></tr>}</tbody></table></section>
  </>}
 </div>;
}

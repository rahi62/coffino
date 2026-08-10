"use client";

import Link from "next/link";
import {FormEvent,useEffect,useMemo,useState} from "react";
import {api} from "@/lib/api";

type Branch={id:number;name:string};
type Product={id:number;branch:number;name:string;is_available:boolean};
type Material={id:number;branch:number;name:string;category:string;material_category_name?:string|null;unit:string;is_active:boolean};
type RecipeItem={id:number;product:number;inventory_item:number;product_name:string;inventory_name:string;quantity:number|string};
type DraftLine={key:string;inventory_item:string;quantity:string};

const branchStorageKey="cafino_settings_branch";
const unitLabels:Record<string,string>={gram:"گرم",kilogram:"کیلوگرم",milliliter:"میلی‌لیتر",liter:"لیتر",piece:"عدد",pack:"بسته"};
const emptyLine=():DraftLine=>({key:`line-${Date.now()}-${Math.random().toString(36).slice(2)}`,inventory_item:"",quantity:"1"});

export default function Recipes(){
 const [products,setProducts]=useState<Product[]>([]),[materials,setMaterials]=useState<Material[]>([]),[rows,setRows]=useState<RecipeItem[]>([]),[branches,setBranches]=useState<Branch[]>([]);
 const [selectedBranchId,setSelectedBranchId]=useState<number|null>(null),[productId,setProductId]=useState(""),[draftLines,setDraftLines]=useState<DraftLine[]>([emptyLine()]);
 const [message,setMessage]=useState(""),[saving,setSaving]=useState(false),[loading,setLoading]=useState(true);

 const load=async()=>{
  setLoading(true);
  try{
   const [nextProducts,nextMaterials,nextRows,nextBranches]=await Promise.all([
    api<Product[]>("/products/"),api<Material[]>("/inventory-items/"),api<RecipeItem[]>("/recipe-items/"),api<Branch[]>("/branches/"),
   ]);
   setProducts(nextProducts);setMaterials(nextMaterials);setRows(nextRows);setBranches(nextBranches);
   setSelectedBranchId(current=>{
    if(current&&nextBranches.some(branch=>branch.id===current))return current;
    const stored=Number(localStorage.getItem(branchStorageKey)||0);
    return nextBranches.some(branch=>branch.id===stored)?stored:nextBranches[0]?.id||null;
   });
  }catch(error:any){setMessage(error.message||"دریافت اطلاعات رسپی انجام نشد.")}finally{setLoading(false)}
 };

 useEffect(()=>{void load()},[]);
 useEffect(()=>{if(selectedBranchId)localStorage.setItem(branchStorageKey,String(selectedBranchId))},[selectedBranchId]);

 const selectedBranch=branches.find(branch=>branch.id===selectedBranchId)||null;
 const branchProducts=useMemo(()=>products.filter(product=>product.branch===selectedBranchId&&product.is_available),[products,selectedBranchId]);
 const branchMaterials=useMemo(()=>materials.filter(material=>material.branch===selectedBranchId),[materials,selectedBranchId]);
 const branchRows=useMemo(()=>rows.filter(row=>products.find(product=>product.id===row.product)?.branch===selectedBranchId),[rows,products,selectedBranchId]);
 const selectedProduct=branchProducts.find(product=>product.id===Number(productId));
 const selectedProductRows=useMemo(()=>branchRows.filter(row=>row.product===Number(productId)),[branchRows,productId]);
 const recipeGroups=useMemo(()=>branchProducts.map(product=>({product,items:branchRows.filter(row=>row.product===product.id)})).filter(group=>group.items.length),[branchProducts,branchRows]);
 const editingExistingRecipe=selectedProductRows.length>0;

 const startRecipe=(nextProductId:string)=>{
  setProductId(nextProductId);
  const savedLines=branchRows.filter(row=>row.product===Number(nextProductId));
  setDraftLines(savedLines.length?savedLines.map(row=>({key:`saved-${row.id}`,inventory_item:String(row.inventory_item),quantity:String(row.quantity)})):[emptyLine()]);
  setMessage("");
 };
 const chooseBranch=(value:string)=>{
  setSelectedBranchId(Number(value));setProductId("");setDraftLines([emptyLine()]);setMessage("");
 };
 const updateLine=(key:string,changes:Partial<DraftLine>)=>setDraftLines(current=>current.map(line=>line.key===key?{...line,...changes}:line));
 const removeLine=(key:string)=>setDraftLines(current=>current.length===1?[{...current[0],inventory_item:"",quantity:"1"}]:current.filter(line=>line.key!==key));
 const editRecipe=(product:number)=>{
  startRecipe(String(product));
  window.scrollTo({top:0,behavior:"smooth"});
 };

 const save=async(event:FormEvent)=>{
  event.preventDefault();
  if(!productId){setMessage("ابتدا محصول رسپی را انتخاب کنید.");return}
  if(!draftLines.length||draftLines.some(line=>!line.inventory_item)){setMessage("برای هر ردیف، یک مادهٔ اولیه انتخاب کنید.");return}
  if(draftLines.some(line=>!line.quantity||Number(line.quantity)<=0)){setMessage("مقدار هر مادهٔ اولیه باید بیشتر از صفر باشد.");return}
  const materialIds=draftLines.map(line=>line.inventory_item);
  if(new Set(materialIds).size!==materialIds.length){setMessage("هر مادهٔ اولیه فقط یک‌بار می‌تواند در رسپی باشد.");return}
  setSaving(true);setMessage("");
  try{
   await api<RecipeItem[]>("/recipe-items/save-recipe/",{method:"PUT",body:JSON.stringify({
    product:Number(productId),ingredients:draftLines.map(line=>({inventory_item:Number(line.inventory_item),quantity:Number(line.quantity)})),
   })});
   setMessage(`رسپی «${selectedProduct?.name||"محصول"}» با ${draftLines.length.toLocaleString("fa-IR")} مادهٔ اولیه ذخیره شد.`);
   await load();
  }catch(error:any){setMessage(error.message||"ذخیرهٔ رسپی انجام نشد.")}finally{setSaving(false)}
 };

 return <div className="space-y-5">
  <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between"><div><h1 className="mb-2 text-3xl font-black">رسپی‌ساز</h1><p className="text-[#8d8178]">برای هر محصول، همهٔ مواد اولیه و مقدار مصرف هرکدام را در یک رسپی ثبت کنید.</p></div><label className="text-sm font-bold">شعبهٔ فعال<select className="btn mr-2 min-w-48" value={selectedBranchId||""} onChange={event=>chooseBranch(event.target.value)} disabled={!branches.length}>{branches.map(branch=><option key={branch.id} value={branch.id}>{branch.name}</option>)}</select></label></div>
  {message&&<div role="status" className="card border-amber-200 p-3">{message}</div>}
  {!loading&&!selectedBranch&&<div className="card p-6">شعبه‌ای برای این کاربر تعریف نشده است.</div>}
  {selectedBranch&&<>
   <form className="card p-5" onSubmit={save}>
    <div className="flex flex-col gap-3 border-b pb-4 md:flex-row md:items-end md:justify-between"><div className="w-full max-w-xl"><label className="text-sm font-bold">محصول رسپی<select className="btn mt-1 w-full" value={productId} onChange={event=>startRecipe(event.target.value)}><option value="">انتخاب محصول</option>{branchProducts.map(product=><option value={product.id} key={product.id}>{product.name}</option>)}</select></label></div>{selectedProduct&&<div className="text-sm text-[#8d8178]">{editingExistingRecipe?"در حال ویرایش رسپی ثبت‌شده":"رسپی جدید"}</div>}</div>
    {!branchMaterials.filter(material=>material.is_active).length&&<div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-4"><div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div><b className="block">هنوز مادهٔ اولیهٔ فعالی برای این شعبه ثبت نشده است.</b><p className="mt-1 text-sm text-[#766858]">برای ساخت رسپی، ابتدا مواد مصرفی را در بخش انبار تعریف کنید.</p></div><Link className="btn btn-primary shrink-0 text-center" href="/inventory">افزودن ماده اولیه</Link></div></div>}
    {selectedProduct&&<div className="mt-5 space-y-3"><div className="flex items-center justify-between gap-3"><div><h2 className="font-black">مواد اولیهٔ «{selectedProduct.name}»</h2><p className="mt-1 text-sm text-[#8d8178]">هر ردیف یک ماده و مقدار مصرف آن برای یک واحد فروش محصول است.</p></div><button type="button" className="btn" onClick={()=>setDraftLines(current=>[...current,emptyLine()])}>افزودن مادهٔ دیگر</button></div>
     <div className="space-y-2">{draftLines.map((line,index)=>{const currentMaterial=branchMaterials.find(material=>material.id===Number(line.inventory_item));const usedElsewhere=draftLines.filter(other=>other.key!==line.key).map(other=>Number(other.inventory_item));return <div className="grid gap-2 rounded-xl border border-[#e9dfd3] p-3 md:grid-cols-[minmax(0,1fr)_180px_auto] md:items-end" key={line.key}><label className="text-sm">مادهٔ اولیهٔ {index+1}<select className="btn mt-1 w-full" value={line.inventory_item} onChange={event=>updateLine(line.key,{inventory_item:event.target.value})}><option value="">انتخاب ماده اولیه</option>{branchMaterials.filter(material=>material.is_active||material.id===Number(line.inventory_item)).map(material=><option value={material.id} key={material.id} disabled={usedElsewhere.includes(material.id)}>{material.name}{material.material_category_name||material.category?` — ${material.material_category_name||material.category}`:""}{material.is_active?"":" (غیرفعال)"}</option>)}</select></label><label className="text-sm">مقدار{currentMaterial?` (${unitLabels[currentMaterial.unit]||currentMaterial.unit})`:""}<input className="btn mt-1 w-full" inputMode="decimal" placeholder="مثلاً ۲۵۰" value={line.quantity} onChange={event=>updateLine(line.key,{quantity:event.target.value})}/></label><button type="button" className="btn text-red-700" onClick={()=>removeLine(line.key)}>{draftLines.length===1?"پاک‌کردن ردیف":"حذف ماده"}</button></div>})}</div>
     <div className="flex flex-col-reverse gap-2 pt-2 sm:flex-row sm:justify-end"><button type="button" className="btn" onClick={()=>startRecipe(productId)}>بازگردانی</button><button className="btn btn-primary disabled:cursor-not-allowed disabled:opacity-50" disabled={saving||!branchMaterials.filter(material=>material.is_active).length}>{saving?"در حال ذخیره…":editingExistingRecipe?"ذخیرهٔ تغییرات رسپی":"ثبت رسپی"}</button></div>
    </div>}
    {!selectedProduct&&<div className="p-8 text-center text-[#8d8178]">محصول را انتخاب کنید تا بتوانید چند مادهٔ اولیه را به رسپی آن اضافه کنید.</div>}
   </form>
   <section><div className="mb-3 flex items-end justify-between"><div><h2 className="text-xl font-black">رسپی‌های ثبت‌شده</h2><p className="mt-1 text-sm text-[#8d8178]">برای تغییر مواد یا مقدار مصرف، گزینهٔ ویرایش را بزنید.</p></div></div>{recipeGroups.length?<div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">{recipeGroups.map(group=><article className="card p-4" key={group.product.id}><div className="flex items-start justify-between gap-3"><b>{group.product.name}</b><button type="button" className="btn text-xs" onClick={()=>editRecipe(group.product.id)}>ویرایش رسپی</button></div><ul className="mt-3 space-y-2 border-t pt-3 text-sm">{group.items.map(item=><li className="flex justify-between gap-3" key={item.id}><span>{item.inventory_name}</span><span className="shrink-0 text-[#8d8178]">{Number(item.quantity).toLocaleString("fa-IR")} {unitLabels[materials.find(material=>material.id===item.inventory_item)?.unit||""]||"واحد"}</span></li>)}</ul></article>)}</div>:<div className="card p-8 text-center text-[#8d8178]">هنوز رسپی‌ای برای محصولات این شعبه ثبت نشده است.</div>}</section>
  </>}
 </div>;
}

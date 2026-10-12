// The backend /permissions/me/ result includes effective role AND module restrictions.
// Unknown/loading/error permissions never unlock a destination.
export const dashboardActions=Object.freeze([
  {href:"/pos",label:"ثبت سفارش جدید",detail:"ورود به فروش",permission:"orders.create"},
  {href:"/orders",label:"سفارش‌ها",detail:"پیگیری سفارش",permission:"orders.view"},
  {href:"/tables",label:"سالن و میزها",detail:"مدیریت میزها",permission:"tables.use"},
  {href:"/cashier",label:"صندوق و شیفت",detail:"وضعیت صندوق",permission:"cashier.use"},
  {href:"/kitchen",label:"آشپزخانه",detail:"صف آماده‌سازی",permission:"kitchen.view"},
  {href:"/products",label:"محصولات و منو",detail:"تعریف محصولات",permission:"inventory.manage"},
  {href:"/reports",label:"گزارش فروش",detail:"گزارش عملکرد",permission:"reports.view"},
  {href:"/settings",label:"تنظیمات کسب‌وکار",detail:"تنظیمات اصلی",permission:"settings.manage"},
]);
export const mobileActions=Object.freeze([
  {href:"/",label:"داشبورد",permission:null},
  {href:"/pos",label:"فروش",permission:"orders.create"},
  {href:"/orders",label:"سفارش‌ها",permission:"orders.view"},
  {href:"/tables",label:"میزها",permission:"tables.use"},
]);
export function permittedActions(actions,permissions){
  if(!permissions)return [];
  return actions.filter(action=>!action.permission||permissions[action.permission]===true);
}
export function routeIsActive(pathname,href){
  return href==="/"?pathname==="/":pathname===href||pathname.startsWith(href+"/");
}

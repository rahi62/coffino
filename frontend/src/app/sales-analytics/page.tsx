"use client";

import {useEffect, useMemo, useState} from "react";
import {BarChart3, BadgePercent, CalendarDays, Download, Package, ReceiptText, RefreshCw, TrendingUp, Undo2} from "lucide-react";
import {LocalizedDateInput} from "@/components/localized-date-input";
import {api} from "@/lib/api";
import {formatLocalizedDate} from "@/lib/calendar";

type SalesRow = {product_name?: string; product__category__name?: string | null; quantity: number | string; revenue: number | string};
type HourRow = {hour: number; orders: number; revenue: number | string};
type DayRow = {day: string; orders: number; revenue: number | string};
type TypeRow = {order_type: string; orders: number; revenue: number | string};
type CashierRow = {received_by__id: number | null; received_by__username?: string; received_by__first_name?: string; transactions: number; refunds: number | string; net_collected: number | string};
type Report = {
  summary: {gross_sales: number | string; refunds: number | string; net_sales: number | string; discounts: number | string; orders: number; items: number | string; average_order_value: number | string};
  by_item: SalesRow[]; by_category: SalesRow[]; by_hour: HourRow[]; by_day: DayRow[]; by_order_type: TypeRow[]; cashiers: CashierRow[];
};

const emptyReport: Report = {summary: {gross_sales: 0, refunds: 0, net_sales: 0, discounts: 0, orders: 0, items: 0, average_order_value: 0}, by_item: [], by_category: [], by_hour: [], by_day: [], by_order_type: [], cashiers: []};
const money = (value: unknown) => Number(value || 0).toLocaleString("fa-IR") + " ریال";
const number = (value: unknown) => Number(value || 0).toLocaleString("fa-IR");
const orderTypeLabel: Record<string, string> = {DINE_IN: "داخل سالن", TAKEAWAY: "بیرون‌بر", PICKUP: "تحویل حضوری", DELIVERY: "ارسال", DRIVE_THROUGH: "دریافت خودرو", CATERING: "کترینگ"};
const colors = ["bg-[#b9792d]", "bg-[#4976a6]", "bg-[#8a5b3d]", "bg-[#5b8b6e]"];

function isoDate(offset = 0) {
  const date = new Date();
  date.setDate(date.getDate() + offset);
  return date.getFullYear() + "-" + String(date.getMonth() + 1).padStart(2, "0") + "-" + String(date.getDate()).padStart(2, "0");
}

export default function SalesAnalytics() {
  const [branches, setBranches] = useState<{id: number; name: string}[]>([]);
  const [branch, setBranch] = useState("");
  const [start, setStart] = useState(() => isoDate(-6));
  const [end, setEnd] = useState(() => isoDate());
  const [period, setPeriod] = useState<"week" | "month" | "quarter" | "custom">("week");
  const [data, setData] = useState<Report>(emptyReport);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  const load = async (branchId: string) => {
    if (!branchId) return;
    setLoading(true);
    try {
      setData(await api<Report>("/reports/sales/?branch=" + encodeURIComponent(branchId) + "&start=" + encodeURIComponent(start) + "&end=" + encodeURIComponent(end)));
      setMessage("");
    } catch (error: any) {
      setMessage(error.message || "دریافت گزارش فروش انجام نشد.");
      setData(emptyReport);
    } finally { setLoading(false); }
  };
  useEffect(() => {
    api<{id: number; name: string}[]>("/branches/").then((items) => { setBranches(items); if (items[0]) setBranch(String(items[0].id)); else setLoading(false); }).catch((error: any) => { setMessage(error.message || "دریافت فهرست شعب انجام نشد."); setLoading(false); });
  }, []);
  useEffect(() => { void load(branch); }, [branch, start, end]);

  const setPreset = (next: "week" | "month" | "quarter" | "custom") => {
    setPeriod(next);
    if (next !== "custom") {
      setStart(isoDate(-(next === "week" ? 6 : next === "month" ? 29 : 89)));
      setEnd(isoDate());
    }
  };
  const days = useMemo(() => data.by_day.slice(-14), [data.by_day]);
  const maxDay = Math.max(...days.map((row) => Number(row.revenue)), 1);
  const maxItem = Math.max(...data.by_item.map((row) => Number(row.revenue)), 1);
  const maxCategory = Math.max(...data.by_category.map((row) => Number(row.revenue)), 1);
  const maxHour = Math.max(...data.by_hour.map((row) => Number(row.revenue)), 1);
  const kpis = [
    ["فروش خالص", money(data.summary.net_sales), number(data.summary.orders) + " سفارش", <TrendingUp size={20} />, "text-[#b9792d] bg-[#fff8ee] border-[#f3dfc4]"],
    ["میانگین هر سفارش", money(data.summary.average_order_value), number(data.summary.items) + " قلم فروخته‌شده", <ReceiptText size={20} />, "text-[#4976a6] bg-[#f3f7fc] border-[#dce8f5]"],
    ["تخفیف ثبت‌شده", money(data.summary.discounts), "جمع تخفیف‌های بازه", <BadgePercent size={20} />, "text-[#8a5b3d] bg-[#fbf5f0] border-[#ead9ca]"],
    ["برگشت وجه", money(data.summary.refunds), "کسرشده از فروش خالص", <Undo2 size={20} />, "text-[#b54f4b] bg-[#fff4f3] border-[#f3d9d7]"],
  ];
  const exportCsv = () => {
    const rows = [["محصول", "تعداد", "فروش"]].concat(data.by_item.map((row) => [row.product_name || "بدون نام", String(row.quantity), String(row.revenue)]));
    const csv = rows.map((row) => row.map((cell) => "\"" + cell.replace(/"/g, "\"\"") + "\"").join(",")).join("\n");
    const url = URL.createObjectURL(new Blob(["\uFEFF" + csv], {type: "text/csv;charset=utf-8"}));
    const link = document.createElement("a"); link.href = url; link.download = "گزارش-فروش.csv"; link.click(); URL.revokeObjectURL(url);
  };

  return <div className="space-y-5">
    <header className="flex flex-col gap-4 rounded-[22px] border border-[#eadfd3] bg-[#fffdf9] p-5 shadow-sm xl:flex-row xl:items-end xl:justify-between">
      <div><p className="mb-1 text-sm font-bold text-[#b9792d]">مالی و گزارش‌ها</p><h1 className="text-3xl font-black">گزارش فروش</h1><p className="mt-2 text-[#8d8178]">روند فروش، محصولات پرفروش، کانال سفارش و عملکرد صندوق‌داران را در یک نما بررسی کنید.</p></div>
      <div className="flex flex-wrap gap-2"><button className="btn" onClick={exportCsv} disabled={!data.by_item.length}><Download size={17} className="ml-1 inline" />خروجی محصولات</button><button className="btn btn-primary" onClick={() => void load(branch)} disabled={loading}><RefreshCw size={17} className={"ml-1 inline " + (loading ? "animate-spin" : "")} />به‌روزرسانی</button></div>
    </header>
    {message && <div role="status" className="card border-r-4 border-r-[#b9792d] p-4">{message}</div>}
    <section className="card p-4"><div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
      <div className="flex flex-wrap gap-2 rounded-xl bg-[#f7f0e8] p-1.5">{([["week", "۷ روز اخیر"], ["month", "۳۰ روز اخیر"], ["quarter", "۹۰ روز اخیر"], ["custom", "بازهٔ دلخواه"]] as const).map(([key, title]) => <button className={"rounded-lg px-3 py-2 text-sm font-bold transition " + (period === key ? "bg-white text-[#211711] shadow-sm" : "text-[#8d8178] hover:text-[#211711]")} key={key} onClick={() => setPreset(key)}>{title}</button>)}</div>
      <div className="grid gap-3 sm:grid-cols-2 xl:flex xl:items-end"><label className="text-sm font-bold">شعبه<select className="btn mt-1 w-full min-w-44" value={branch} onChange={(event) => setBranch(event.target.value)}>{branches.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}</select></label>{period === "custom" ? <div className="grid grid-cols-2 gap-2"><label className="text-sm font-bold">از تاریخ<LocalizedDateInput className="mt-1" value={start} onChange={setStart} /></label><label className="text-sm font-bold">تا تاریخ<LocalizedDateInput className="mt-1" value={end} onChange={setEnd} /></label></div> : <div className="rounded-xl border border-[#eadfd3] bg-white px-4 py-2 text-sm text-[#8d8178]"><CalendarDays size={16} className="ml-1 inline text-[#b9792d]" />{formatLocalizedDate(start)} تا {formatLocalizedDate(end)}</div>}</div>
    </div></section>
    {loading ? <div className="card p-10 text-center text-[#8d8178]">در حال آماده‌سازی گزارش فروش…</div> : <>
      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{kpis.map(([label, value, detail, icon, tone]) => <article className={"rounded-2xl border p-4 " + tone} key={String(label)}><div className="mb-3 grid size-10 place-items-center rounded-xl bg-white shadow-sm">{icon}</div><p className="text-sm font-bold text-[#6f6259]">{label}</p><b className="mt-2 block text-xl text-[#211711]">{value}</b><p className="mt-1 text-xs text-[#8d8178]">{detail}</p></article>)}</section>
      <section className="grid gap-4 xl:grid-cols-[minmax(0,1.45fr)_minmax(320px,.75fr)]">
        <article className="card p-5"><div className="flex items-start justify-between gap-3"><div><h2 className="font-black text-lg">روند فروش روزانه</h2><p className="mt-1 text-sm text-[#8d8178]">فروش ثبت‌شده در بازهٔ انتخاب‌شده</p></div><span className="badge">{number(data.summary.orders)} سفارش</span></div>{days.length ? <div className="mt-6 flex h-52 items-end gap-2">{days.map((row) => <div className="group flex h-full min-w-0 flex-1 flex-col justify-end" key={row.day}><div className="relative rounded-t-lg bg-[#b9792d] transition group-hover:bg-[#8f581c]" style={{height: Math.max((Number(row.revenue) / maxDay) * 100, 4) + "%"}}><span className="absolute -top-7 right-1/2 hidden w-max translate-x-1/2 rounded-lg bg-[#211711] px-2 py-1 text-[10px] text-white group-hover:block">{money(row.revenue)}</span></div><span className="mt-2 truncate text-center text-[10px] text-[#8d8178]">{new Intl.DateTimeFormat("fa-IR-u-ca-persian", {month: "numeric", day: "numeric"}).format(new Date(row.day + "T12:00:00"))}</span></div>)}</div> : <Empty label="در این بازه فروشی برای نمایش وجود ندارد." />}</article>
        <article className="card p-5"><h2 className="font-black text-lg">کانال فروش</h2><p className="mt-1 text-sm text-[#8d8178]">تفکیک بر اساس روش ثبت سفارش</p><div className="mt-5 space-y-4">{data.by_order_type.length ? data.by_order_type.map((row, index) => <Progress key={row.order_type} label={orderTypeLabel[row.order_type] || row.order_type} value={money(row.revenue)} percent={Number(row.revenue) / Math.max(Number(data.summary.gross_sales), 1) * 100} color={colors[index % colors.length]} />) : <Empty label="داده‌ای برای کانال فروش وجود ندارد." />}</div></article>
      </section>
      <section className="grid gap-4 xl:grid-cols-2">
        <article className="card p-5"><div className="flex items-center justify-between"><div><h2 className="font-black text-lg">محصولات پرفروش</h2><p className="mt-1 text-sm text-[#8d8178]">رتبه‌بندی بر اساس مبلغ فروش</p></div><Package size={21} className="text-[#b9792d]" /></div><div className="mt-5 space-y-4">{data.by_item.length ? data.by_item.slice(0, 8).map((row, index) => <div key={row.product_name}><div className="flex items-center justify-between gap-3 text-sm"><span className="min-w-0 truncate font-bold"><i className="ml-2 inline-flex size-6 items-center justify-center rounded-lg bg-[#f7f0e8] text-xs not-italic text-[#b9792d]">{number(index + 1)}</i>{row.product_name}</span><span className="shrink-0 text-xs text-[#8d8178]">{number(row.quantity)} عدد · <b className="text-[#211711]">{money(row.revenue)}</b></span></div><div className="mt-2 h-1.5 overflow-hidden rounded-full bg-[#f1e9e1]"><div className="h-full rounded-full bg-[#b9792d]" style={{width: Number(row.revenue) / maxItem * 100 + "%"}} /></div></div>) : <Empty label="هنوز محصولی در این بازه فروخته نشده است." />}</div></article>
        <article className="card p-5"><div className="flex items-center justify-between"><div><h2 className="font-black text-lg">دسته‌بندی‌ها</h2><p className="mt-1 text-sm text-[#8d8178]">سهم هر دسته از فروش اقلام</p></div><BarChart3 size={21} className="text-[#4976a6]" /></div><div className="mt-5 space-y-4">{data.by_category.length ? data.by_category.map((row, index) => <Progress key={row.product__category__name || "none"} label={row.product__category__name || "بدون دسته‌بندی"} value={money(row.revenue)} percent={Number(row.revenue) / maxCategory * 100} color={colors[index % colors.length]} />) : <Empty label="دسته‌بندی فروشی ثبت نشده است." />}</div></article>
      </section>
      <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(360px,.8fr)]">
        <article className="card p-5"><h2 className="font-black text-lg">اوج فروش ساعتی</h2><p className="mt-1 text-sm text-[#8d8178]">مقایسهٔ مبلغ فروش در ساعت‌های مختلف</p>{data.by_hour.length ? <div className="mt-6 grid grid-cols-6 gap-x-3 gap-y-4 sm:grid-cols-8 lg:grid-cols-12">{data.by_hour.map((row) => <div className="group text-center" key={row.hour}><div className="flex h-20 items-end rounded-lg bg-[#f7f0e8] p-1"><div className="w-full rounded-md bg-[#8a5b3d] transition group-hover:bg-[#b9792d]" style={{height: Math.max(Number(row.revenue) / maxHour * 100, 8) + "%"}} /></div><b className="mt-2 block text-xs">{number(row.hour)}:۰۰</b><span className="text-[10px] text-[#8d8178]">{number(row.orders)} سفارش</span></div>)}</div> : <Empty label="اطلاعات ساعتی برای این بازه وجود ندارد." />}</article>
        <article className="card overflow-hidden"><div className="border-b border-[#eadfd3] p-5"><h2 className="font-black text-lg">عملکرد صندوق‌داران</h2><p className="mt-1 text-sm text-[#8d8178]">دریافت خالص و تعداد تراکنش‌ها</p></div><div className="divide-y divide-[#f0e8df]">{data.cashiers.length ? data.cashiers.map((row) => <div className="flex items-center justify-between gap-3 p-4" key={row.received_by__id || row.received_by__username}><div className="min-w-0"><b className="block truncate">{row.received_by__first_name || row.received_by__username || "نامشخص"}</b><span className="text-xs text-[#8d8178]">{number(row.transactions)} تراکنش · برگشت {money(row.refunds)}</span></div><b className="shrink-0 text-sm text-[#211711]">{money(row.net_collected)}</b></div>) : <Empty label="تراکنش صندوق‌داری برای این بازه ثبت نشده است." />}</div></article>
      </section>
    </>}
  </div>;
}

function Progress({label, value, percent, color}: {label: string; value: string; percent: number; color: string}) {
  return <div><div className="flex items-center justify-between gap-3 text-sm"><b className="truncate">{label}</b><span className="shrink-0 text-xs text-[#6f6259]">{value}</span></div><div className="mt-2 h-2 overflow-hidden rounded-full bg-[#f1e9e1]"><div className={"h-full rounded-full " + color} style={{width: Math.max(Math.min(percent, 100), 2) + "%"}} /></div></div>;
}
function Empty({label}: {label: string}) { return <div className="grid min-h-36 place-items-center text-center text-sm text-[#8d8178]"><span>{label}</span></div>; }

"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { formatLocalizedDate } from "@/lib/calendar";

type KpiData = {
  start: string;
  end: string;
  orders: number;
  net_revenue: number | string;
  average_ticket: number | string;
  gross_margin_percent: number | string | null;
  food_cost_percent: number | string | null;
  refund_rate_percent: number | string | null;
  labor_hours: number | string | null;
  sales_per_labor_hour: number | string | null;
  cash_variance_absolute: number | string;
  waste_cost: number | string;
  low_stock_count: number;
  break_even_revenue: number | string | null;
  top_product?: { product_name: string; quantity: number | string; revenue: number | string };
};

const dash = "—";
const number = (value: number | string | null | undefined, fractionDigits = 0) =>
  value == null ? dash : new Intl.NumberFormat("fa-IR", { maximumFractionDigits: fractionDigits, minimumFractionDigits: fractionDigits }).format(Number(value));
const money = (value: number | string | null | undefined) => value == null ? dash : `${number(value)} ریال`;
const percent = (value: number | string | null | undefined) => value == null ? dash : `${number(value, 1)}٪`;

export default function KPI() {
  const [data, setData] = useState<KpiData | null>(null);
  const [message, setMessage] = useState("");

  useEffect(() => {
    api<KpiData>("/reports/kpi/").then(setData).catch((caught) => setMessage(caught instanceof Error ? caught.message : "دریافت شاخص‌ها انجام نشد."));
  }, []);

  if (!data) return <div className="card p-5">{message || "در حال محاسبه شاخص‌های مدیریتی…"}</div>;

  const cards: Array<[string, string]> = [
    ["درآمد خالص", money(data.net_revenue)],
    ["میانگین مبلغ سفارش", money(data.average_ticket)],
    ["حاشیه سود ناخالص", percent(data.gross_margin_percent)],
    ["بهای مواد مصرفی", percent(data.food_cost_percent)],
    ["نرخ بازگشت وجه", percent(data.refund_rate_percent)],
    ["ساعت کار", number(data.labor_hours, 1)],
    ["فروش به‌ازای هر ساعت کار", money(data.sales_per_labor_hour)],
    ["مغایرت مطلق صندوق", money(data.cash_variance_absolute)],
    ["هزینه ضایعات", money(data.waste_cost)],
    ["تعداد اقلام کم‌موجود", number(data.low_stock_count)],
    ["فروش لازم برای سربه‌سر", money(data.break_even_revenue)],
    ["تعداد سفارش", number(data.orders)],
  ];

  return (
    <div>
      <h1 className="mb-2 text-3xl font-black">شاخص‌های مدیریتی</h1>
      <p className="mb-5 text-[#8d8178]">از {formatLocalizedDate(data.start)} تا {formatLocalizedDate(data.end)}</p>
      <div className="grid gap-4 md:grid-cols-3 xl:grid-cols-4">
        {cards.map(([title, value]) => <div className="card p-4" key={title}><div className="text-sm text-[#8d8178]">{title}</div><b className="mt-2 block text-xl">{value}</b></div>)}
      </div>
      {data.top_product && <div className="card mt-5 p-5"><div className="text-[#8d8178]">پرفروش‌ترین محصول</div><b className="text-2xl">{data.top_product.product_name}</b><div className="mt-2">{number(data.top_product.quantity)} عدد یا واحد — {money(data.top_product.revenue)} فروش ناخالص این محصول</div></div>}
    </div>
  );
}

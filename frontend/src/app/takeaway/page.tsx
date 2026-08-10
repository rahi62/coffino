"use client";

import { ShoppingBag } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { label } from "@/lib/i18n";

type Pager = { id: number; status: string };
type TakeawayOrder = {
  id: number;
  order_number: string | number;
  status: string;
  items?: Array<{ id: number; quantity: number; product_name: string }>;
  takeaway?: { id: number; pager_number?: string | number; ready_notification_method?: "SMS" | "PAGER" | "NONE"; notified_at?: string | null };
};

export default function Takeaway() {
  const [orders, setOrders] = useState<TakeawayOrder[]>([]);
  const [pagers, setPagers] = useState<Pager[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async () => {
    try {
      const [rows, devices] = await Promise.all([
        api<TakeawayOrder[]>("/orders/?order_type=TAKEAWAY"),
        api<Pager[]>("/pagers/"),
      ]);
      setOrders(rows);
      setPagers(devices);
      setError("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "دریافت سفارش‌های بیرون‌بر انجام نشد.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { void load(); }, []);

  async function assignPager(order: TakeawayOrder) {
    const freePager = pagers.find((pager) => pager.status === "AVAILABLE");
    if (!freePager || !order.takeaway) return;
    try {
      await api(`/takeaway-profiles/${order.takeaway.id}/assign_pager/`, {
        method: "POST",
        body: JSON.stringify({ pager_id: freePager.id }),
      });
      await load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "اختصاص پیجر انجام نشد.");
    }
  }

  return (
    <div>
      <h1 className="mb-5 text-3xl font-black">صف بیرون‌بر</h1>
      {error && <div className="card mb-4 border border-red-200 p-3 text-red-700">{error}</div>}
      {isLoading ? (
        <div className="card p-8 text-center text-[#8d8178]">در حال دریافت سفارش‌های بیرون‌بر…</div>
      ) : orders.length === 0 ? (
        <section className="card flex min-h-56 flex-col items-center justify-center p-8 text-center" aria-live="polite">
          <div className="mb-4 rounded-full bg-[#eee6dc] p-4 text-[#b9792d]">
            <ShoppingBag className="h-8 w-8" aria-hidden="true" />
          </div>
          <h2 className="text-xl font-black">سفارش بیرون‌بری وجود ندارد</h2>
          <p className="mt-2 max-w-md leading-7 text-[#8d8178]">
            سفارش‌های بیرون‌بر پس از ثبت در بخش فروش، در این صفحه برای پیگیری و اختصاص پیجر نمایش داده می‌شوند.
          </p>
        </section>
      ) : (
        <div className="grid gap-4 md:grid-cols-3">
          {orders.map((order) => (
            <article className="card p-5" key={order.id}>
              <div className="flex justify-between gap-3"><b className="text-2xl">#{order.order_number}</b><span className="badge">{label(order.status)}</span></div>
              <div className="mt-4 text-sm">{order.items?.map((item) => <div key={item.id}>{item.quantity} × {item.product_name}</div>)}</div>
              <div className="mt-4">
                {order.takeaway?.ready_notification_method === "PAGER" ? (order.takeaway.pager_number ? `پیجر ${order.takeaway.pager_number}` : <button className="btn" onClick={() => void assignPager(order)}>اختصاص پیجر</button>) : order.takeaway?.ready_notification_method === "SMS" ? "پیامک پس از آماده‌شدن سفارش" : "بدون اعلان آماده‌شدن"}
              </div>
              {order.takeaway?.notified_at && <div className="mt-2 text-xs text-emerald-700">اعلان آماده‌شدن سفارش ارسال شده است.</div>}
            </article>
          ))}
        </div>
      )}
    </div>
  );
}

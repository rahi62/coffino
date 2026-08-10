"use client";

import { ChefHat, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { label } from "@/lib/i18n";

type KitchenTicket = {
  id: number;
  order_number: string | number;
  order_type: string;
  order_status: string;
  payment_status: string;
  fulfillment_destination: string;
  ready_notification_method?: "SMS" | "PAGER" | "NONE" | null;
  ready_notification_status?: string | null;
  station_name: string;
  status: "NEW" | "PREPARING" | "READY" | "DONE";
  items?: Array<{ id: number; quantity: number; product_name: string; notes?: string }>;
};

const paymentClasses: Record<string, string> = {
  UNPAID: "bg-red-50 text-red-800",
  PARTIALLY_PAID: "bg-amber-50 text-amber-800",
  PAID: "bg-emerald-50 text-emerald-800",
  PARTIALLY_REFUNDED: "bg-sky-50 text-sky-800",
  REFUNDED: "bg-[#eee6dc] text-[#766858]",
};

export default function Kitchen() {
  const [tickets, setTickets] = useState<KitchenTicket[]>([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [updatingTicketId, setUpdatingTicketId] = useState<number | null>(null);

  const loadTickets = async (showLoading = false) => {
    if (showLoading) setIsLoading(true);
    try {
      const rows = await api<KitchenTicket[]>("/kitchen-tickets/");
      setTickets(rows.filter((ticket) => ticket.status !== "DONE"));
      setError("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "دریافت سفارش‌های آشپزخانه انجام نشد.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadTickets(true);
    const interval = window.setInterval(() => void loadTickets(), 5000);
    return () => window.clearInterval(interval);
  }, []);

  async function updateTicket(id: number, action: "preparing" | "ready" | "done") {
    setUpdatingTicketId(id);
    setError("");
    setMessage("");
    try {
      const updated=await api<KitchenTicket>(`/kitchen-tickets/${id}/${action}/`, { method: "POST" });
      await loadTickets();
      if (action === "ready") {
        const delivery=updated.ready_notification_method==="SMS"?"پیامک آماده‌شدن سفارش در صف ارسال قرار گرفت.":updated.ready_notification_method==="PAGER"?"فرمان فراخوانی پیجر در صف ارسال قرار گرفت.":"سفارش آمادهٔ تحویل است.";
        setMessage(delivery);
      }
      if (action === "done") setMessage("تحویل سفارش ثبت شد.");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "به‌روزرسانی وضعیت سفارش انجام نشد.");
    } finally {
      setUpdatingTicketId(null);
    }
  }

  async function printTicket(id: number) {
    try {
      const job = await api<{ id: number; payload: unknown }>(`/kitchen-tickets/${id}/print-job/`, {
        method: "POST",
        body: "{}",
      });
      const cafino = window as Window & {
        cafino?: { printKitchen: (payload: unknown, device: string) => Promise<{ ok: boolean; error?: string }> };
      };
      const device = localStorage.getItem("cafino_kitchen_printer") || "";
      if (!cafino.cafino?.printKitchen) {
        setMessage("چاپ مستقیم تیکت فقط در برنامه دسکتاپ کافینو در دسترس است.");
        return;
      }

      const result = await cafino.cafino.printKitchen(job.payload, device);
      if (result.ok) {
        await api(`/print-jobs/${job.id}/mark_printed/`, { method: "POST", body: "{}" });
        setMessage("تیکت چاپ و ثبت شد.");
      } else {
        await api(`/print-jobs/${job.id}/mark_failed/`, {
          method: "POST",
          body: JSON.stringify({ error: result.error }),
        });
        setError(result.error || "چاپ تیکت انجام نشد.");
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "ساخت یا چاپ تیکت انجام نشد.");
    }
  }

  return (
    <div>
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="mb-2 text-3xl font-black">نمایشگر آشپزخانه</h1>
          <p className="text-[#8d8178]">پیگیری و آماده‌سازی سفارش‌های هر ایستگاه</p>
        </div>
        <button className="btn inline-flex items-center gap-2" onClick={() => void loadTickets(true)} disabled={isLoading}>
          <RefreshCw className={isLoading ? "h-4 w-4 animate-spin" : "h-4 w-4"} aria-hidden="true" />
          تازه‌سازی
        </button>
      </div>

      {message && <div className="card mb-4 p-3 text-green-800">{message}</div>}
      {error && <div className="card mb-4 border border-red-200 p-3 text-red-700">{error}</div>}

      {isLoading && tickets.length === 0 ? (
        <div className="card p-8 text-center text-[#8d8178]">در حال دریافت سفارش‌های آشپزخانه…</div>
      ) : tickets.length === 0 ? (
        <section className="card flex min-h-56 flex-col items-center justify-center p-8 text-center" aria-live="polite">
          <div className="mb-4 rounded-full bg-[#eee6dc] p-4 text-[#b9792d]">
            <ChefHat className="h-8 w-8" aria-hidden="true" />
          </div>
          <h2 className="text-xl font-black">سفارش در حال آماده‌سازی وجود ندارد</h2>
          <p className="mt-2 max-w-md leading-7 text-[#8d8178]">
            پس از ثبت و پرداخت سفارش دارای محصولِ متصل به ایستگاه آماده‌سازی، تیکت آن به‌صورت خودکار در این بخش نمایش داده می‌شود.
          </p>
          <p className="mt-3 text-sm text-[#8d8178]">این صفحه هر ۵ ثانیه به‌صورت خودکار به‌روزرسانی می‌شود.</p>
        </section>
      ) : (
        <div className="grid gap-4 md:grid-cols-3">
          {tickets.map((ticket) => (
            <article className="card border-t-4 border-t-[#b9792d] p-5" key={ticket.id}>
              <div className="mb-4 flex justify-between gap-3">
                <b className="text-2xl">#{ticket.order_number}</b>
                <span className="badge">{ticket.station_name} • {label(ticket.status)}</span>
              </div>
              <div className="mb-4 flex flex-wrap gap-2 text-xs font-bold">
                <span className="rounded-full bg-sky-50 px-2 py-1 text-sky-800">وضعیت سفارش: {label(ticket.order_status)}</span>
                <span className={`rounded-full px-2 py-1 ${paymentClasses[ticket.payment_status] || "bg-[#eee6dc] text-[#766858]"}`}>وضعیت پرداخت: {label(ticket.payment_status)}</span>
              </div>
              <div className="mb-4 rounded-xl bg-[#eee6dc] p-3 text-sm"><b>محل/روش تحویل: </b>{ticket.fulfillment_destination}{ticket.status === "READY" && ticket.ready_notification_method && ticket.ready_notification_method !== "NONE" && <div className="mt-1 text-xs text-[#766858]">وضعیت اعلان: {ticket.ready_notification_status ? label(ticket.ready_notification_status) : "در انتظار ثبت"}</div>}</div>
              {ticket.items?.map((item) => (
                <div className="border-b py-2" key={item.id}>
                  <b>{item.quantity} × {item.product_name}</b>
                  {item.notes && <div className="text-sm">{item.notes}</div>}
                </div>
              ))}
              <div className="mt-4 flex flex-wrap gap-2">
                <button className="btn" onClick={() => void printTicket(ticket.id)} disabled={updatingTicketId === ticket.id}>چاپ</button>
                {ticket.status === "NEW" && <button className="btn" onClick={() => void updateTicket(ticket.id, "preparing")} disabled={updatingTicketId === ticket.id}>شروع آماده‌سازی</button>}
                {ticket.status !== "READY" && <button className="btn btn-primary" onClick={() => void updateTicket(ticket.id, "ready")} disabled={updatingTicketId === ticket.id}>آماده و اطلاع‌رسانی</button>}
                {ticket.status === "READY" && <button className="btn btn-primary" onClick={() => void updateTicket(ticket.id, "done")} disabled={updatingTicketId === ticket.id}>{updatingTicketId === ticket.id ? "در حال ثبت تحویل…" : ticket.order_type === "DINE_IN" ? "تحویل به گارسون" : "تحویل سفارش"}</button>}
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}

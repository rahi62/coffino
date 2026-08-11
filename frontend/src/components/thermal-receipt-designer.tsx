"use client";

export type DocumentType = "RECEIPT" | "KITCHEN" | "BAR";
export type ThermalLayout = {paper_width?: 58 | 80; blocks?: string[]};

const labels: Record<string, string> = {
  business: "نام کسب‌وکار",
  header: "متن آغاز",
  order: "شماره و زمان سفارش",
  customer: "مشتری",
  items: "جدول اقلام",
  summary: "جمع، تخفیف و مالیات",
  payment: "روش پرداخت",
  barcode: "بارکد سفارش",
  footer: "متن پایان",
};

const receiptBlocks = ["business", "header", "order", "customer", "items", "summary", "payment", "barcode", "footer"];
const ticketBlocks = ["business", "header", "order", "items", "footer"];

export function defaultReceiptLayout(type: DocumentType): Required<ThermalLayout> {
  return {
    paper_width: 80,
    blocks: type === "RECEIPT" ? receiptBlocks : ticketBlocks,
  };
}

export function normalizeReceiptLayout(value: ThermalLayout | undefined, type: DocumentType): Required<ThermalLayout> {
  const defaults = defaultReceiptLayout(type);
  const allowed = new Set(defaults.blocks);
  const blocks = (value?.blocks || []).filter((block) => allowed.has(block));
  return {
    paper_width: value?.paper_width === 58 ? 58 : 80,
    blocks: blocks.length ? blocks : defaults.blocks,
  };
}

export function ThermalReceiptPreview({
  layout,
  type,
  template,
  id,
}: {
  layout?: ThermalLayout;
  type: DocumentType;
  template?: {header?: string; footer?: string; show_customer?: boolean; show_tax?: boolean; show_service_charge?: boolean};
  id?: string;
}) {
  const normalized = normalizeReceiptLayout(layout, type);
  const isReceipt = type === "RECEIPT";
  const show = (block: string) => normalized.blocks.includes(block);
  const divider = <div className="my-2 border-t border-dashed border-[#8d8178]" />;

  return (
    <div className="rounded-xl bg-[#eee6dc] p-4">
      <div
        id={id}
        className="mx-auto bg-white p-3 text-[10px] text-[#211711] shadow"
        style={{width: normalized.paper_width === 58 ? 192 : 272, fontFamily: "Tahoma, sans-serif"}}
      >
        {show("business") && <b className="block text-center text-sm">کافینو</b>}
        {show("header") && template?.header && <p className="mt-1 whitespace-pre-line text-center">{template.header}</p>}
        {(show("business") || (show("header") && template?.header)) && divider}
        {show("order") && <div className="flex justify-between"><span>سفارش ۱۲۳</span><span>۱۴۰۵/۰۵/۲۰</span></div>}
        {show("customer") && isReceipt && template?.show_customer !== false && <div className="mt-1">مشتری: نمونه</div>}
        {show("items") && <div className="my-2 space-y-1">{isReceipt ? <><div className="flex justify-between"><span>۲ × لاته</span><span>۵۰۰٬۰۰۰</span></div><div className="flex justify-between"><span>۱ × کیک</span><span>۳۰۰٬۰۰۰</span></div></> : <><b className="block">۲ × لاته</b><b className="block">۱ × کیک</b></>}</div>}
        {show("summary") && isReceipt && <><div className="border-t border-dashed border-[#8d8178] pt-2">{template?.show_service_charge !== false && <div className="flex justify-between"><span>حق سرویس</span><span>۰</span></div>}{template?.show_tax !== false && <div className="flex justify-between"><span>مالیات</span><span>۰</span></div>}<b className="mt-1 flex justify-between text-xs"><span>قابل پرداخت</span><span>۸۰۰٬۰۰۰ ریال</span></b></div></>}
        {show("payment") && isReceipt && <><div className="my-2 border-t border-dashed border-[#8d8178]" /><span>پرداخت: کارت‌خوان</span></>}
        {show("barcode") && isReceipt && <div className="mt-2 text-center tracking-[3px]">||| |||| |||</div>}
        {show("footer") && template?.footer && <p className="mt-3 whitespace-pre-line text-center">{template.footer}</p>}
      </div>
    </div>
  );
}

export default function ThermalReceiptDesigner({
  value,
  onChange,
  type,
  template,
}: {
  value: ThermalLayout | undefined;
  onChange: (next: Required<ThermalLayout>) => void;
  type: DocumentType;
  template?: {header?: string; footer?: string; show_customer?: boolean; show_tax?: boolean; show_service_charge?: boolean};
}) {
  const layout = normalizeReceiptLayout(value, type);
  const allowed = defaultReceiptLayout(type).blocks;
  const active = layout.blocks;
  const update = (blocks: string[] = active, paperWidth: 58 | 80 = layout.paper_width) => onChange({paper_width: paperWidth, blocks});
  const move = (index: number, direction: -1 | 1) => {
    const next = [...active];
    const target = index + direction;
    if (target < 0 || target >= next.length) return;
    [next[index], next[target]] = [next[target], next[index]];
    update(next);
  };

  return (
    <section className="rounded-2xl border border-[#eadfd3] bg-[#fffdf9] p-4 sm:col-span-2">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h3 className="font-black">طراح فیش حرارتی</h3>
          <p className="mt-1 text-xs text-[#8d8178]">بلوک‌ها را به ترتیب چاپ بچینید. عرض پیش‌نمایش با کاغذ انتخابی منطبق است.</p>
        </div>
        <div className="flex gap-2">
          <button type="button" className={`btn text-xs ${layout.paper_width === 80 ? "btn-primary" : ""}`} onClick={() => update(active, 80)}>۸۰ میلی‌متر</button>
          <button type="button" className={`btn text-xs ${layout.paper_width === 58 ? "btn-primary" : ""}`} onClick={() => update(active, 58)}>۵۸ میلی‌متر</button>
        </div>
      </div>
      <div className="mt-4 grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(220px,.75fr)]">
        <div>
          <p className="mb-2 text-xs font-bold text-[#8d8178]">بلوک‌های فیش</p>
          <div className="space-y-2">
            {active.map((block, index) => <div className="flex items-center justify-between rounded-xl border border-[#eadfd3] bg-white px-3 py-2 text-sm" key={block}>
              <span>{labels[block]}</span>
              <div className="flex gap-1">
                <button type="button" className="btn px-2 text-xs" aria-label="انتقال به بالا" onClick={() => move(index, -1)}>↑</button>
                <button type="button" className="btn px-2 text-xs" aria-label="انتقال به پایین" onClick={() => move(index, 1)}>↓</button>
                <button type="button" className="btn px-2 text-xs text-red-700" aria-label="حذف بلوک" onClick={() => update(active.filter((_, itemIndex) => itemIndex !== index))}>×</button>
              </div>
            </div>)}
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            {allowed.filter((block) => !active.includes(block)).map((block) => <button type="button" className="btn text-xs" key={block} onClick={() => update([...active, block])}>+ {labels[block]}</button>)}
          </div>
        </div>
        <ThermalReceiptPreview layout={layout} type={type} template={template} />
      </div>
    </section>
  );
}

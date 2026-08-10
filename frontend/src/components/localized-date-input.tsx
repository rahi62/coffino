"use client";

import { useMemo, useState } from "react";
import { CalendarDays, ChevronLeft, ChevronRight } from "lucide-react";
import { CalendarDate, gregorianToJalali, isJalaliLeapYear, isJalaliLocale, jalaliToGregorian, parseDateValue, serializeDate } from "@/lib/calendar";

type Props = { value: string; onChange: (value: string) => void; className?: string; withTime?: boolean; disabled?: boolean };

const faMonths = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"];
const enMonths = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const faWeekdays = ["ش", "ی", "د", "س", "چ", "پ", "ج"];
const enWeekdays = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];

function daysInMonth(year: number, month: number, jalali: boolean) {
  if (!jalali) return new Date(year, month, 0).getDate();
  if (month <= 6) return 31;
  if (month <= 11) return 30;
  return isJalaliLeapYear(year) ? 30 : 29;
}

function weekday(date: CalendarDate, jalali: boolean) {
  const g = jalali ? jalaliToGregorian(date) : date;
  const native = new Date(g.year, g.month - 1, g.day).getDay();
  return jalali ? (native + 1) % 7 : native;
}

function normalize(year: number, month: number) {
  if (month < 1) return { year: year - 1, month: 12 };
  if (month > 12) return { year: year + 1, month: 1 };
  return { year, month };
}

export function LocalizedDateInput({ value, onChange, className = "", withTime = false, disabled = false }: Props) {
  const jalali = isJalaliLocale();
  const parsed = parseDateValue(value);
  const selected = parsed?.date;
  const calendarSelected = selected ? (jalali ? gregorianToJalali(selected) : selected) : undefined;
  const today = new Date();
  const initial = calendarSelected ?? (jalali ? gregorianToJalali({ year: today.getFullYear(), month: today.getMonth() + 1, day: today.getDate() }) : { year: today.getFullYear(), month: today.getMonth() + 1, day: today.getDate() });
  const [view, setView] = useState({ year: initial.year, month: initial.month });
  const [open, setOpen] = useState(false);
  const months = jalali ? faMonths : enMonths;
  const weekdays = jalali ? faWeekdays : enWeekdays;
  const dayCount = daysInMonth(view.year, view.month, jalali);
  const emptyCells = weekday({ year: view.year, month: view.month, day: 1 }, jalali);
  const display = calendarSelected ? `${calendarSelected.year}/${String(calendarSelected.month).padStart(2, "0")}/${String(calendarSelected.day).padStart(2, "0")}` : "انتخاب تاریخ";

  const cells = useMemo(() => Array.from({ length: emptyCells + dayCount }, (_, index) => index < emptyCells ? null : index - emptyCells + 1), [emptyCells, dayCount]);
  function choose(day: number) {
    const calendarDate = { year: view.year, month: view.month, day };
    const gregorian = jalali ? jalaliToGregorian(calendarDate) : calendarDate;
    onChange(`${serializeDate(gregorian)}${withTime ? `T${parsed?.time || "00:00"}` : ""}`);
    setOpen(false);
  }
  function changeTime(time: string) {
    const fallback = selected ?? { year: today.getFullYear(), month: today.getMonth() + 1, day: today.getDate() };
    onChange(`${serializeDate(fallback)}T${time}`);
  }
  function move(delta: number) { setView(current => normalize(current.year, current.month + delta)); }

  return <div className={`relative ${className}`}>
    <div className="flex min-w-0 gap-2">
      <button type="button" disabled={disabled} onClick={() => setOpen(v => !v)} className="border rounded-xl p-2 text-right flex min-w-0 flex-1 items-center justify-between gap-2 disabled:opacity-50" aria-haspopup="dialog" aria-expanded={open}>
        <span className="truncate">{display}</span><CalendarDays size={17} aria-hidden="true" />
      </button>
      {withTime && <input type="time" className="border rounded-xl p-2 w-28" value={parsed?.time || ""} onChange={event => changeTime(event.target.value)} disabled={disabled} aria-label="زمان" />}
    </div>
    {open && <div className="absolute z-50 mt-2 w-72 rounded-2xl border border-[#eadfd3] bg-white p-3 shadow-xl" role="dialog" aria-label="انتخاب تاریخ">
      <div className="mb-3 flex items-center justify-between"><button type="button" className="btn !p-2" onClick={() => move(-1)} aria-label="ماه قبل"><ChevronRight size={18} /></button><b>{months[view.month - 1]} {view.year}</b><button type="button" className="btn !p-2" onClick={() => move(1)} aria-label="ماه بعد"><ChevronLeft size={18} /></button></div>
      <div className="grid grid-cols-7 gap-1 text-center text-xs text-[#8d8178]">{weekdays.map(day => <span key={day}>{day}</span>)}</div>
      <div className="mt-1 grid grid-cols-7 gap-1">{cells.map((day, index) => day === null ? <span key={`empty-${index}`} /> : <button type="button" key={day} onClick={() => choose(day)} className={`aspect-square rounded-lg text-sm hover:bg-[#eee6dc] ${calendarSelected?.year === view.year && calendarSelected.month === view.month && calendarSelected.day === day ? "bg-[#b9792d] text-white hover:bg-[#a96320]" : ""}`}>{day}</button>)}</div>
    </div>}
  </div>;
}

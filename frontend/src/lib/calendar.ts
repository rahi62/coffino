import { getLocale } from "@/lib/i18n";

export type CalendarDate = { year: number; month: number; day: number };

const breaks = [-61, 9, 38, 199, 426, 686, 756, 818, 1111, 1181, 1210, 1630, 2060, 2097, 2192, 2262, 2324, 2394, 2456, 3178];
const div = (a: number, b: number) => Math.trunc(a / b);
const mod = (a: number, b: number) => a - Math.trunc(a / b) * b;

function jalCal(jy: number, withoutLeap = false) {
  let leapJ = -14;
  let jp = breaks[0];
  let jm = 0;
  let jump = 0;
  if (jy < jp || jy >= breaks.at(-1)!) throw new Error("سال انتخاب‌شده معتبر نیست.");
  for (let i = 1; i < breaks.length; i += 1) {
    jm = breaks[i]; jump = jm - jp;
    if (jy < jm) break;
    leapJ += div(jump, 33) * 8 + div(mod(jump, 33), 4);
    jp = jm;
  }
  let n = jy - jp;
  leapJ += div(n, 33) * 8 + div(mod(n, 33) + 3, 4);
  if (mod(jump, 33) === 4 && jump - n === 4) leapJ += 1;
  const gy = jy + 621;
  const leapG = div(gy, 4) - div((div(gy, 100) + 1) * 3, 4) - 150;
  const march = 20 + leapJ - leapG;
  if (withoutLeap) return { gy, march };
  if (jump - n < 6) n = n - jump + div(jump + 4, 33) * 33;
  let leap = mod(mod(n + 1, 33) - 1, 4);
  if (leap === -1) leap = 4;
  return { leap, gy, march };
}

function g2d(gy: number, gm: number, gd: number) {
  let d = div((gy + div(gm - 8, 6) + 100100) * 1461, 4) + div(153 * mod(gm + 9, 12) + 2, 5) + gd - 34840408;
  d -= div(div(gy + 100100 + div(gm - 8, 6), 100) * 3, 4) - 752;
  return d;
}

function d2g(jdn: number): CalendarDate {
  let j = 4 * jdn + 139361631;
  j += div(div(4 * jdn + 183187720, 146097) * 3, 4) * 4 - 3908;
  const i = div(mod(j, 1461), 4) * 5 + 308;
  return { year: div(j, 1461) - 100100 + div(8 - (mod(div(i, 153), 12) + 1), 6), month: mod(div(i, 153), 12) + 1, day: div(mod(i, 153), 5) + 1 };
}

function j2d(jy: number, jm: number, jd: number) {
  const r = jalCal(jy, true);
  return g2d(r.gy, 3, r.march) + (jm - 1) * 31 - div(jm, 7) * (jm - 7) + jd - 1;
}

function d2j(jdn: number): CalendarDate {
  const g = d2g(jdn);
  let year = g.year - 621;
  const r = jalCal(year);
  const jdn1f = g2d(g.year, 3, r.march);
  let k = jdn - jdn1f;
  if (k >= 0) {
    if (k <= 185) return { year, month: 1 + div(k, 31), day: mod(k, 31) + 1 };
    k -= 186;
  } else {
    year -= 1; k += 179;
    if (r.leap === 1) k += 1;
  }
  return { year, month: 7 + div(k, 30), day: mod(k, 30) + 1 };
}

export function gregorianToJalali(date: CalendarDate): CalendarDate { return d2j(g2d(date.year, date.month, date.day)); }
export function jalaliToGregorian(date: CalendarDate): CalendarDate { return d2g(j2d(date.year, date.month, date.day)); }
export function isJalaliLeapYear(year: number) { return jalCal(year).leap === 0; }
export function isJalaliLocale() { return getLocale() === "fa"; }

export function parseDateValue(value: string): { date: CalendarDate; time: string } | null {
  const match = /^(\d{4})-(\d{2})-(\d{2})(?:T(\d{2}:\d{2}))?/.exec(value || "");
  return match ? { date: { year: Number(match[1]), month: Number(match[2]), day: Number(match[3]) }, time: match[4] || "00:00" } : null;
}

export function serializeDate(date: CalendarDate) {
  return `${date.year.toString().padStart(4, "0")}-${date.month.toString().padStart(2, "0")}-${date.day.toString().padStart(2, "0")}`;
}

export function formatLocalizedDate(value: string | Date, withTime = false) {
  const date = typeof value === "string" ? new Date(value) : value;
  if (Number.isNaN(date.getTime())) return "—";
  const locale = isJalaliLocale() ? "fa-IR-u-ca-persian" : "en-GB";
  return new Intl.DateTimeFormat(locale, withTime ? { dateStyle: "medium", timeStyle: "short" } : { dateStyle: "medium" }).format(date);
}

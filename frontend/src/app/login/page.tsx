"use client";

import {useState} from "react";
import {Coffee, Eye, EyeOff, Package, ShieldCheck, ShoppingCart, UsersRound} from "lucide-react";
import {login} from "@/lib/api";

const weekBars = [38, 56, 44, 72, 51, 66, 88];

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!username.trim() || !password) {
      setError("نام کاربری و رمز عبور را وارد کنید.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await login(username.trim(), password);
      location.assign("/");
    } catch (cause: any) {
      setError(cause?.message || "ورود انجام نشد. اطلاعات ورود را بررسی و دوباره تلاش کنید.");
    } finally {
      setBusy(false);
    }
  }

  return <div className="fixed inset-0 z-50 flex min-h-screen overflow-hidden bg-[#f0ece6]">
    <section className="flex w-full items-center justify-center bg-[#fffdf9] px-6 py-10 sm:px-10 lg:w-[46%] lg:min-w-[420px] lg:px-14">
      <form className="w-full max-w-[330px]" onSubmit={submit} noValidate>
        <div className="mb-10 flex items-center gap-3">
          <div className="grid size-11 place-items-center rounded-2xl bg-[#211711] text-xl text-white shadow-lg shadow-[#211711]/15"><Coffee size={21} aria-hidden="true" /></div>
          <div><p className="text-lg font-black tracking-[-.4px] text-[#211711]">کافینو</p><p className="text-xs text-[#8d8178]">مدیریت هوشمند پذیرایی</p></div>
        </div>

        <div className="mb-8">
          <h1 className="text-3xl font-black tracking-[-.7px] text-[#211711]">خوش آمدید</h1>
          <p className="mt-2 text-sm text-[#8d8178]">برای ورود به پنل مدیریت، اطلاعات خود را وارد کنید.</p>
        </div>

        <div className="space-y-4">
          <label className="block text-sm font-bold text-[#51453d]">نام کاربری
            <input
              autoComplete="username"
              autoFocus
              className="mt-2 h-12 w-full rounded-xl border border-[#e6ddd3] bg-[#faf7f2] px-4 text-left text-sm text-[#211711] outline-none transition focus:border-[#b9792d] focus:bg-white focus:ring-4 focus:ring-[#b9792d]/10"
              dir="ltr"
              value={username}
              onChange={(event) => { setUsername(event.target.value); setError(""); }}
              placeholder="نام کاربری"
            />
          </label>
          <label className="block text-sm font-bold text-[#51453d]">رمز عبور
            <span className="relative mt-2 block">
              <input
                autoComplete="current-password"
                className="h-12 w-full rounded-xl border border-[#e6ddd3] bg-[#faf7f2] py-0 pl-12 pr-4 text-left text-sm text-[#211711] outline-none transition focus:border-[#b9792d] focus:bg-white focus:ring-4 focus:ring-[#b9792d]/10"
                dir="ltr"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(event) => { setPassword(event.target.value); setError(""); }}
                placeholder="رمز عبور"
              />
              <button type="button" className="absolute left-2 top-1/2 grid size-9 -translate-y-1/2 place-items-center rounded-lg text-[#8d8178] transition hover:bg-[#eee6dc] hover:text-[#211711] focus-visible:outline focus-visible:outline-3 focus-visible:outline-[#b9792d]/35" onClick={() => setShowPassword((current) => !current)} aria-label={showPassword ? "پنهان‌کردن رمز عبور" : "نمایش رمز عبور"}>
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </span>
          </label>
        </div>

        {error && <div role="alert" className="mt-4 rounded-xl border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-800">{error}</div>}

        <button className="mt-6 h-12 w-full rounded-xl bg-[#211711] px-4 text-sm font-bold text-white shadow-lg shadow-[#211711]/15 transition hover:bg-[#3b2b20] disabled:cursor-not-allowed disabled:opacity-60" disabled={busy} type="submit">
          {busy ? "در حال ورود…" : "ورود به پنل"}
        </button>
        <div className="mt-5 flex items-center gap-2 text-xs leading-5 text-[#8d8178]"><ShieldCheck size={16} className="shrink-0 text-[#b9792d]" /><span>دسترسی شما بر اساس نقش و شعبهٔ فعال کنترل می‌شود.</span></div>
      </form>
    </section>

    <aside className="relative hidden flex-1 overflow-hidden bg-[#ede7df] p-8 lg:block">
      <div className="absolute inset-0 opacity-50" style={{backgroundImage: "radial-gradient(circle, rgba(58,43,32,.16) 1px, transparent 1px)", backgroundSize: "22px 22px"}} />
      <div className="relative mx-auto flex h-full max-w-[660px] flex-col justify-center gap-3">
        <div className="grid grid-cols-[1.15fr_1fr] gap-3">
          <article className="rounded-3xl bg-[#211711] p-5 text-white shadow-xl shadow-[#211711]/10">
            <div className="mb-4 flex items-center gap-2 text-xs font-bold text-white/55"><span className="size-2 rounded-full bg-emerald-400 shadow-[0_0_10px_#4ade80]" />سامانه فعال</div>
            <p className="font-mono text-2xl font-black tracking-[.16em]">۱۲:۴۵:۲۸</p>
          </article>
          <article className="rounded-3xl border border-[#e6ddd3] bg-white p-5">
            <p className="text-xs font-bold text-[#8d8178]">فروش امروز</p>
            <p className="mt-2 text-2xl font-black tracking-[-1px] text-[#211711]">۲٬۵۴۱٬۰۰۰</p>
            <p className="mt-1 text-xs font-bold text-emerald-600">↑ ۱۲٪ نسبت به دیروز</p>
          </article>
        </div>

        <article className="rounded-3xl border border-[#e6ddd3] bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center justify-between"><h2 className="text-sm font-black text-[#211711]">عملکرد هفته</h2><span className="rounded-full bg-[#f7f0e8] px-3 py-1 text-xs font-bold text-[#b9792d]">۷ روز</span></div>
          <div className="flex h-16 items-end gap-1.5">{weekBars.map((height, index) => <span className={index === weekBars.length - 1 ? "flex-1 rounded-t-md bg-[#211711]" : index === 4 ? "flex-1 rounded-t-md bg-[#b9792d]" : "flex-1 rounded-t-md bg-[#e9dfd3]"} key={height} style={{height: `${height}%`}} />)}</div>
          <div className="mt-2 flex justify-between text-[10px] font-bold text-[#9b9087]"><span>ش</span><span>ی</span><span>د</span><span>س</span><span>چ</span><span>پ</span><span>ج</span></div>
        </article>

        <div className="grid grid-cols-3 gap-3">
          <Metric icon={<ShoppingCart size={19} />} label="سفارش" value="۸۵" detail="امروز" color="bg-[#b9792d]" />
          <Metric icon={<UsersRound size={19} />} label="مشتری" value="۱۲" detail="فعال" color="bg-[#4976a6]" />
          <Metric icon={<Package size={19} />} label="کم‌موجودی" value="۲" detail="آیتم" color="bg-[#8a5b3d]" />
        </div>

        <article className="rounded-3xl border border-[#e6ddd3] bg-white p-5">
          <div className="mb-3 flex items-center justify-between"><h2 className="text-sm font-black text-[#211711]">روند فروش</h2><span className="text-xs font-bold text-emerald-600">↑ ۱۲٪</span></div>
          <svg viewBox="0 0 300 66" className="h-16 w-full overflow-visible" aria-label="روند افزایشی فروش" role="img"><defs><linearGradient id="login-sales-area" x1="0" x2="0" y1="0" y2="1"><stop stopColor="#b9792d" stopOpacity=".24" /><stop offset="1" stopColor="#b9792d" stopOpacity="0" /></linearGradient></defs><path d="M0,55 C35,49 52,54 82,34 C110,14 137,39 166,25 C196,10 220,30 248,16 C266,7 284,12 300,5 L300,66 L0,66Z" fill="url(#login-sales-area)" /><path d="M0,55 C35,49 52,54 82,34 C110,14 137,39 166,25 C196,10 220,30 248,16 C266,7 284,12 300,5" fill="none" stroke="#b9792d" strokeLinecap="round" strokeWidth="3" /></svg>
        </article>
      </div>
    </aside>
  </div>;
}

function Metric({icon, label, value, detail, color}: {icon: React.ReactNode; label: string; value: string; detail: string; color: string}) {
  return <article className={`rounded-2xl p-4 text-center text-white shadow-lg ${color}`}><div className="mx-auto mb-2 grid size-8 place-items-center rounded-xl bg-white/15">{icon}</div><p className="text-[11px] font-bold text-white/70">{label}</p><p className="mt-1 text-2xl font-black">{value}</p><p className="text-[10px] text-white/65">{detail}</p></article>;
}

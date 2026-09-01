"use client";

import {useEffect, useState} from "react";
import {Coffee, Eye, EyeOff, Package, ShieldCheck, ShoppingCart, UsersRound} from "lucide-react";
import {localBootstrap, localBootstrapStatus, login} from "@/lib/api";

const weekBars = [38, 56, 44, 72, 51, 66, 88];
type LoginMode = "checking" | "login" | "setup";

export default function Login() {
  const [mode, setMode] = useState<LoginMode>("checking");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const [businessName, setBusinessName] = useState("");
  const [branchName, setBranchName] = useState("شعبه اصلی");
  const [businessType, setBusinessType] = useState("CAFE");
  const [ownerUsername, setOwnerUsername] = useState("owner");
  const [ownerEmail, setOwnerEmail] = useState("");
  const [ownerPassword, setOwnerPassword] = useState("");
  const [ownerPasswordConfirmation, setOwnerPasswordConfirmation] = useState("");
  const [showOwnerPassword, setShowOwnerPassword] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));
    async function detectFirstRun() {
      const hasElectronBridge = typeof window !== "undefined" && Boolean((window as any).cafino);
      const attempts = hasElectronBridge ? 60 : 1;
      for (let attempt = 0; attempt < attempts; attempt++) {
        try {
          const status = await localBootstrapStatus();
          if (cancelled) return;
          setMode(status?.available && status.needs_setup ? "setup" : "login");
          return;
        } catch {
          if (attempt < attempts - 1) {
            await sleep(500);
            continue;
          }
          if (!cancelled) setMode("login");
        }
      }
    }
    detectFirstRun();
    return () => { cancelled = true; };
  }, []);

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

  async function submitSetup(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    const cleanBusiness = businessName.trim();
    const cleanBranch = branchName.trim();
    const cleanUsername = ownerUsername.trim();
    if (!cleanBusiness || !cleanBranch || !cleanUsername) {
      setError("نام کسب‌وکار، شعبه و نام کاربری مالک را کامل کنید.");
      return;
    }
    if (ownerPassword.length < 12 || !/[A-Za-z]/.test(ownerPassword) || !/\d/.test(ownerPassword)) {
      setError("رمز مالک باید حداقل ۱۲ کاراکتر و شامل حداقل یک حرف لاتین و یک عدد باشد.");
      return;
    }
    if (ownerPassword !== ownerPasswordConfirmation) {
      setError("تکرار رمز عبور با رمز مالک یکسان نیست.");
      return;
    }
    setBusy(true);
    try {
      await localBootstrap({
        business_name: cleanBusiness,
        branch_name: cleanBranch,
        business_type: businessType,
        username: cleanUsername,
        email: ownerEmail.trim(),
        password: ownerPassword,
        password_confirmation: ownerPasswordConfirmation,
      });
      await login(cleanUsername, ownerPassword);
      location.assign("/");
    } catch (cause: any) {
      const message = String(cause?.message || "راه‌اندازی اولیه انجام نشد.");
      setError(message);
      if (message.includes("already been initialized") || message.includes("setup is closed")) setMode("login");
    } finally {
      setBusy(false);
    }
  }

  return <div className="fixed inset-0 z-50 flex min-h-screen overflow-hidden bg-[#f0ece6]">
    <section className="flex w-full items-center justify-center overflow-y-auto bg-[#fffdf9] px-6 py-10 sm:px-10 lg:w-[46%] lg:min-w-[420px] lg:px-14">
      <div className="w-full max-w-[360px]">
        <div className="mb-8 flex items-center gap-3">
          <div className="grid size-11 place-items-center rounded-2xl bg-[#211711] text-xl text-white shadow-lg shadow-[#211711]/15"><Coffee size={21} aria-hidden="true" /></div>
          <div><p className="text-lg font-black tracking-[-.4px] text-[#211711]">کافینو</p><p className="text-xs text-[#8d8178]">مدیریت هوشمند پذیرایی</p></div>
        </div>

        {mode === "checking" && <div className="rounded-3xl border border-[#e6ddd3] bg-white p-6 shadow-sm">
          <div className="mb-3 size-8 animate-pulse rounded-xl bg-[#b9792d]/20" />
          <h1 className="text-xl font-black text-[#211711]">در حال آماده‌سازی کافینو…</h1>
          <p className="mt-2 text-sm leading-6 text-[#8d8178]">وضعیت Backend و نصب اولیه بررسی می‌شود.</p>
        </div>}

        {mode === "login" && <form onSubmit={submit} noValidate>
          <div className="mb-8">
            <h1 className="text-3xl font-black tracking-[-.7px] text-[#211711]">خوش آمدید</h1>
            <p className="mt-2 text-sm text-[#8d8178]">برای ورود به پنل مدیریت، اطلاعات خود را وارد کنید.</p>
          </div>

          <div className="space-y-4">
            <label className="block text-sm font-bold text-[#51453d]">نام کاربری
              <input autoComplete="username" autoFocus className="mt-2 h-12 w-full rounded-xl border border-[#e6ddd3] bg-[#faf7f2] px-4 text-left text-sm text-[#211711] outline-none transition focus:border-[#b9792d] focus:bg-white focus:ring-4 focus:ring-[#b9792d]/10" dir="ltr" value={username} onChange={(event) => { setUsername(event.target.value); setError(""); }} placeholder="نام کاربری" />
            </label>
            <label className="block text-sm font-bold text-[#51453d]">رمز عبور
              <span className="relative mt-2 block">
                <input autoComplete="current-password" className="h-12 w-full rounded-xl border border-[#e6ddd3] bg-[#faf7f2] py-0 pl-12 pr-4 text-left text-sm text-[#211711] outline-none transition focus:border-[#b9792d] focus:bg-white focus:ring-4 focus:ring-[#b9792d]/10" dir="ltr" type={showPassword ? "text" : "password"} value={password} onChange={(event) => { setPassword(event.target.value); setError(""); }} placeholder="رمز عبور" />
                <button type="button" className="absolute left-2 top-1/2 grid size-9 -translate-y-1/2 place-items-center rounded-lg text-[#8d8178] transition hover:bg-[#eee6dc] hover:text-[#211711]" onClick={() => setShowPassword((current) => !current)} aria-label={showPassword ? "پنهان‌کردن رمز عبور" : "نمایش رمز عبور"}>{showPassword ? <EyeOff size={18} /> : <Eye size={18} />}</button>
              </span>
            </label>
          </div>

          {error && <div role="alert" className="mt-4 rounded-xl border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-800">{error}</div>}
          <button className="mt-6 h-12 w-full rounded-xl bg-[#211711] px-4 text-sm font-bold text-white shadow-lg shadow-[#211711]/15 transition hover:bg-[#3b2b20] disabled:cursor-not-allowed disabled:opacity-60" disabled={busy} type="submit">{busy ? "در حال ورود…" : "ورود به پنل"}</button>
          <div className="mt-5 flex items-center gap-2 text-xs leading-5 text-[#8d8178]"><ShieldCheck size={16} className="shrink-0 text-[#b9792d]" /><span>دسترسی شما بر اساس نقش و شعبهٔ فعال کنترل می‌شود.</span></div>
        </form>}

        {mode === "setup" && <form onSubmit={submitSetup} noValidate>
          <div className="mb-6">
            <span className="inline-flex rounded-full bg-[#f6eadb] px-3 py-1 text-xs font-black text-[#a46722]">راه‌اندازی اولیه Local</span>
            <h1 className="mt-3 text-3xl font-black tracking-[-.7px] text-[#211711]">کافینو را آماده کنید</h1>
            <p className="mt-2 text-sm leading-6 text-[#8d8178]">این مرحله فقط روی دیتابیس کاملاً تازه فعال است و اولین کسب‌وکار، شعبه و حساب مالک را می‌سازد.</p>
          </div>

          <div className="grid gap-3">
            <label className="block text-sm font-bold text-[#51453d]">نام کسب‌وکار
              <input autoFocus className="mt-1.5 h-11 w-full rounded-xl border border-[#e6ddd3] bg-[#faf7f2] px-3 outline-none focus:border-[#b9792d] focus:bg-white" value={businessName} onChange={(e)=>{setBusinessName(e.target.value);setError("")}} placeholder="مثلاً کافه رکسان" />
            </label>
            <div className="grid grid-cols-2 gap-3">
              <label className="block text-sm font-bold text-[#51453d]">شعبه
                <input className="mt-1.5 h-11 w-full rounded-xl border border-[#e6ddd3] bg-[#faf7f2] px-3 outline-none focus:border-[#b9792d] focus:bg-white" value={branchName} onChange={(e)=>{setBranchName(e.target.value);setError("")}} />
              </label>
              <label className="block text-sm font-bold text-[#51453d]">نوع مجموعه
                <select className="mt-1.5 h-11 w-full rounded-xl border border-[#e6ddd3] bg-[#faf7f2] px-2 outline-none focus:border-[#b9792d] focus:bg-white" value={businessType} onChange={(e)=>setBusinessType(e.target.value)}>
                  <option value="CAFE">کافه</option><option value="RESTAURANT">رستوران</option><option value="FAST_FOOD">فست‌فود</option><option value="BAKERY">نانوایی/قنادی</option><option value="CATERING">کترینگ</option>
                </select>
              </label>
            </div>
            <label className="block text-sm font-bold text-[#51453d]">نام کاربری مالک
              <input autoComplete="username" dir="ltr" className="mt-1.5 h-11 w-full rounded-xl border border-[#e6ddd3] bg-[#faf7f2] px-3 text-left outline-none focus:border-[#b9792d] focus:bg-white" value={ownerUsername} onChange={(e)=>{setOwnerUsername(e.target.value);setError("")}} />
            </label>
            <label className="block text-sm font-bold text-[#51453d]">ایمیل مالک <span className="font-normal text-[#a39890]">(اختیاری)</span>
              <input autoComplete="email" dir="ltr" type="email" className="mt-1.5 h-11 w-full rounded-xl border border-[#e6ddd3] bg-[#faf7f2] px-3 text-left outline-none focus:border-[#b9792d] focus:bg-white" value={ownerEmail} onChange={(e)=>setOwnerEmail(e.target.value)} placeholder="owner@example.com" />
            </label>
            <label className="block text-sm font-bold text-[#51453d]">رمز مالک
              <span className="relative mt-1.5 block">
                <input autoComplete="new-password" dir="ltr" type={showOwnerPassword?"text":"password"} className="h-11 w-full rounded-xl border border-[#e6ddd3] bg-[#faf7f2] py-0 pl-11 pr-3 text-left outline-none focus:border-[#b9792d] focus:bg-white" value={ownerPassword} onChange={(e)=>{setOwnerPassword(e.target.value);setError("")}} placeholder="حداقل ۱۲ کاراکتر" />
                <button type="button" className="absolute left-1 top-1/2 grid size-9 -translate-y-1/2 place-items-center rounded-lg text-[#8d8178]" onClick={()=>setShowOwnerPassword(v=>!v)} aria-label="نمایش یا پنهان کردن رمز">{showOwnerPassword?<EyeOff size={17}/>:<Eye size={17}/>}</button>
              </span>
            </label>
            <label className="block text-sm font-bold text-[#51453d]">تکرار رمز مالک
              <input autoComplete="new-password" dir="ltr" type={showOwnerPassword?"text":"password"} className="mt-1.5 h-11 w-full rounded-xl border border-[#e6ddd3] bg-[#faf7f2] px-3 text-left outline-none focus:border-[#b9792d] focus:bg-white" value={ownerPasswordConfirmation} onChange={(e)=>{setOwnerPasswordConfirmation(e.target.value);setError("")}} />
            </label>
          </div>

          {error && <div role="alert" className="mt-4 rounded-xl border border-red-200 bg-red-50 px-3 py-2.5 text-sm leading-6 text-red-800">{error}</div>}
          <button className="mt-5 h-12 w-full rounded-xl bg-[#211711] px-4 text-sm font-bold text-white shadow-lg shadow-[#211711]/15 transition hover:bg-[#3b2b20] disabled:cursor-not-allowed disabled:opacity-60" disabled={busy} type="submit">{busy?"در حال ساخت حساب مالک…":"ساخت کافینو و ورود"}</button>
          <div className="mt-4 flex items-start gap-2 rounded-xl bg-[#f7f3ee] p-3 text-xs leading-5 text-[#75685f]"><ShieldCheck size={16} className="mt-0.5 shrink-0 text-[#b9792d]" /><span>پس از ساخت اولین حساب، این مسیر برای همین دیتابیس برای همیشه بسته می‌شود.</span></div>
        </form>}
      </div>
    </section>

    <aside className="relative hidden flex-1 overflow-hidden bg-[#ede7df] p-8 lg:block">
      <div className="absolute inset-0 opacity-50" style={{backgroundImage: "radial-gradient(circle, rgba(58,43,32,.16) 1px, transparent 1px)", backgroundSize: "22px 22px"}} />
      <div className="relative mx-auto flex h-full max-w-[660px] flex-col justify-center gap-3">
        <div className="grid grid-cols-[1.15fr_1fr] gap-3">
          <article className="rounded-3xl bg-[#211711] p-5 text-white shadow-xl shadow-[#211711]/10"><div className="mb-4 flex items-center gap-2 text-xs font-bold text-white/55"><span className="size-2 rounded-full bg-emerald-400 shadow-[0_0_10px_#4ade80]" />سامانه فعال</div><p className="font-mono text-2xl font-black tracking-[.16em]">۱۲:۴۵:۲۸</p></article>
          <article className="rounded-3xl border border-[#e6ddd3] bg-white p-5"><p className="text-xs font-bold text-[#8d8178]">فروش امروز</p><p className="mt-2 text-2xl font-black tracking-[-1px] text-[#211711]">۲٬۵۴۱٬۰۰۰</p><p className="mt-1 text-xs font-bold text-emerald-600">↑ ۱۲٪ نسبت به دیروز</p></article>
        </div>
        <article className="rounded-3xl border border-[#e6ddd3] bg-white p-5 shadow-sm"><div className="mb-4 flex items-center justify-between"><h2 className="text-sm font-black text-[#211711]">عملکرد هفته</h2><span className="rounded-full bg-[#f7f0e8] px-3 py-1 text-xs font-bold text-[#b9792d]">۷ روز</span></div><div className="flex h-16 items-end gap-1.5">{weekBars.map((height, index) => <span className={index === weekBars.length - 1 ? "flex-1 rounded-t-md bg-[#211711]" : index === 4 ? "flex-1 rounded-t-md bg-[#b9792d]" : "flex-1 rounded-t-md bg-[#e9dfd3]"} key={`${height}-${index}`} style={{height: `${height}%`}} />)}</div><div className="mt-2 flex justify-between text-[10px] font-bold text-[#9b9087]"><span>ش</span><span>ی</span><span>د</span><span>س</span><span>چ</span><span>پ</span><span>ج</span></div></article>
        <div className="grid grid-cols-3 gap-3"><Metric icon={<ShoppingCart size={19} />} label="سفارش" value="۸۵" detail="امروز" color="bg-[#b9792d]" /><Metric icon={<UsersRound size={19} />} label="مشتری" value="۱۲" detail="فعال" color="bg-[#4976a6]" /><Metric icon={<Package size={19} />} label="کم‌موجودی" value="۲" detail="آیتم" color="bg-[#8a5b3d]" /></div>
        <article className="rounded-3xl border border-[#e6ddd3] bg-white p-5"><div className="mb-3 flex items-center justify-between"><h2 className="text-sm font-black text-[#211711]">روند فروش</h2><span className="text-xs font-bold text-emerald-600">↑ ۱۲٪</span></div><svg viewBox="0 0 300 66" className="h-16 w-full overflow-visible" aria-label="روند افزایشی فروش" role="img"><defs><linearGradient id="login-sales-area" x1="0" x2="0" y1="0" y2="1"><stop stopColor="#b9792d" stopOpacity=".24" /><stop offset="1" stopColor="#b9792d" stopOpacity="0" /></linearGradient></defs><path d="M0,55 C35,49 52,54 82,34 C110,14 137,39 166,25 C196,10 220,30 248,16 C266,7 284,12 300,5 L300,66 L0,66Z" fill="url(#login-sales-area)" /><path d="M0,55 C35,49 52,54 82,34 C110,14 137,39 166,25 C196,10 220,30 248,16 C266,7 284,12 300,5" fill="none" stroke="#b9792d" strokeLinecap="round" strokeWidth="3" /></svg></article>
      </div>
    </aside>
  </div>;
}

function Metric({icon, label, value, detail, color}: {icon: React.ReactNode; label: string; value: string; detail: string; color: string}) {
  return <article className={`rounded-2xl p-4 text-center text-white shadow-lg ${color}`}><div className="mx-auto mb-2 grid size-8 place-items-center rounded-xl bg-white/15">{icon}</div><p className="text-[11px] font-bold text-white/70">{label}</p><p className="mt-1 text-2xl font-black">{value}</p><p className="text-[10px] text-white/65">{detail}</p></article>;
}

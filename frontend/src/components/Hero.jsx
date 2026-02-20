export default function Hero() {
  return (
    <section className="max-w-7xl mx-auto px-6 pt-20 pb-14 md:pt-24 md:pb-20">
      <div className="relative overflow-hidden rounded-3xl border border-slate-200/70 dark:border-slate-800 bg-white/70 dark:bg-slate-950/40 backdrop-blur-sm">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute -top-24 -left-24 h-72 w-72 rounded-full bg-blue-500/15 blur-3xl aa-float" />
          <div className="absolute -bottom-28 -right-24 h-80 w-80 rounded-full bg-cyan-400/10 blur-3xl aa-float" />
        </div>

        <div className="relative px-6 py-14 md:px-12 md:py-20 text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-slate-200/70 dark:border-slate-800 bg-white/70 dark:bg-slate-900/30 px-4 py-2 text-xs font-semibold tracking-wide text-slate-600 dark:text-slate-300 aa-fade-up">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            Verified reports • GPS validated • Camera-only
          </div>

          <h2 className="mt-6 text-4xl md:text-6xl font-extrabold text-slate-900 dark:text-white leading-tight tracking-tight aa-fade-up-2">
            Secure & Smart
            <br />
            <span className="bg-gradient-to-r from-blue-600 to-cyan-500 bg-clip-text text-transparent">Water & Pollution</span> Monitoring
          </h2>

          <p className="mt-6 text-base md:text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto leading-relaxed aa-fade-up-2">
            AquaAlert helps citizens report issues with live camera evidence and accurate GPS, then routes work through supervisors and field workers with end-to-end verification.
          </p>

          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-3">
            <a
              href="/login.html?role=user"
              className="w-full sm:w-auto inline-flex items-center justify-center rounded-xl bg-slate-900 text-white px-5 py-3 text-sm font-semibold shadow-sm hover:bg-slate-800 active:scale-[0.99] transition"
            >
              Submit a Report
            </a>
            <a
              href="/login.html?role=supervisor"
              className="w-full sm:w-auto inline-flex items-center justify-center rounded-xl border border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/30 px-5 py-3 text-sm font-semibold text-slate-700 dark:text-slate-200 hover:bg-white dark:hover:bg-slate-900/50 active:scale-[0.99] transition"
            >
              Supervisor Dashboard
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
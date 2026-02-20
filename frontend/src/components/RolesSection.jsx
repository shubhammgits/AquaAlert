export default function RolesSection() {
  return (
    <section aria-label="Portals" className="max-w-5xl mx-auto px-6 min-h-screen flex items-center">
      <div className="w-full space-y-4">
        <a
          href="/login.html?role=supervisor"
          className="group block rounded-2xl border border-slate-200/70 dark:border-slate-800 bg-white/70 dark:bg-slate-950/40 backdrop-blur-sm p-6 md:p-7 transition hover:shadow-xl"
        >
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
            <div className="min-w-0">
              <div className="flex items-center gap-3">
                <span className="inline-flex h-9 w-9 items-center justify-center rounded-xl bg-blue-600/10 text-blue-700 dark:text-blue-300 border border-blue-600/20">
                  01
                </span>
                <h3 className="text-xl md:text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                  Supervisor
                </h3>
              </div>
              <p className="mt-3 text-slate-600 dark:text-slate-400 leading-relaxed">
                High-level oversight for data verification, trend analysis, and administrative reporting.
              </p>
              <div className="mt-4 flex flex-wrap gap-2 text-xs">
                <span className="rounded-full border border-slate-200 dark:border-slate-800 px-3 py-1 text-slate-600 dark:text-slate-300">Live monitoring dashboard</span>
                <span className="rounded-full border border-slate-200 dark:border-slate-800 px-3 py-1 text-slate-600 dark:text-slate-300">Image & GPS verification</span>
                <span className="rounded-full border border-slate-200 dark:border-slate-800 px-3 py-1 text-slate-600 dark:text-slate-300">Automated flood alerts</span>
              </div>
            </div>

            <div className="shrink-0">
              <span className="inline-flex items-center justify-center rounded-xl bg-blue-600 text-white px-5 py-3 text-sm font-semibold shadow-sm transition group-hover:bg-blue-700">
                Access Admin Panel
              </span>
            </div>
          </div>
        </a>

        <a
          href="/login.html?role=worker"
          className="group block rounded-2xl border border-slate-200/70 dark:border-slate-800 bg-white/70 dark:bg-slate-950/40 backdrop-blur-sm p-6 md:p-7 transition hover:shadow-xl"
        >
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
            <div className="min-w-0">
              <div className="flex items-center gap-3">
                <span className="inline-flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-600/10 text-emerald-700 dark:text-emerald-300 border border-emerald-600/20">
                  02
                </span>
                <h3 className="text-xl md:text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                  Field Worker
                </h3>
              </div>
              <p className="mt-3 text-slate-600 dark:text-slate-400 leading-relaxed">
                Reliable data entry from site locations with mandatory biometric and geo-tagging.
              </p>
              <div className="mt-4 flex flex-wrap gap-2 text-xs">
                <span className="rounded-full border border-slate-200 dark:border-slate-800 px-3 py-1 text-slate-600 dark:text-slate-300">Geofencing validation</span>
                <span className="rounded-full border border-slate-200 dark:border-slate-800 px-3 py-1 text-slate-600 dark:text-slate-300">Mandatory live photo</span>
                <span className="rounded-full border border-slate-200 dark:border-slate-800 px-3 py-1 text-slate-600 dark:text-slate-300">Offline synchronization</span>
              </div>
            </div>

            <div className="shrink-0">
              <span className="inline-flex items-center justify-center rounded-xl bg-emerald-600 text-white px-5 py-3 text-sm font-semibold shadow-sm transition group-hover:bg-emerald-700">
                Worker Portal
              </span>
            </div>
          </div>
        </a>

        <a
          href="/login.html?role=user"
          className="group block rounded-2xl border border-slate-200/70 dark:border-slate-800 bg-white/70 dark:bg-slate-950/40 backdrop-blur-sm p-6 md:p-7 transition hover:shadow-xl"
        >
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
            <div className="min-w-0">
              <div className="flex items-center gap-3">
                <span className="inline-flex h-9 w-9 items-center justify-center rounded-xl bg-slate-900/5 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-800">
                  03
                </span>
                <h3 className="text-xl md:text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                  Public Source
                </h3>
              </div>
              <p className="mt-3 text-slate-600 dark:text-slate-400 leading-relaxed">
                Empowering citizens to contribute to community safety through crowdsourced images.
              </p>
              <div className="mt-4 flex flex-wrap gap-2 text-xs">
                <span className="rounded-full border border-slate-200 dark:border-slate-800 px-3 py-1 text-slate-600 dark:text-slate-300">Fast image upload</span>
                <span className="rounded-full border border-slate-200 dark:border-slate-800 px-3 py-1 text-slate-600 dark:text-slate-300">Auto-location tagging</span>
                <span className="rounded-full border border-slate-200 dark:border-slate-800 px-3 py-1 text-slate-600 dark:text-slate-300">Anonymous reporting</span>
              </div>
            </div>

            <div className="shrink-0">
              <span className="inline-flex items-center justify-center rounded-xl bg-slate-900 text-white px-5 py-3 text-sm font-semibold shadow-sm transition group-hover:bg-slate-800">
                Submit Observation
              </span>
            </div>
          </div>
        </a>
      </div>
    </section>
  );
}
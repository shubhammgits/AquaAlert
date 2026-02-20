export default function RoleCard({ title, description, features, buttonText, theme, href }) {
  const themes = {
    blue: {
      shell:
        "border-blue-100/70 dark:border-blue-900/50 bg-blue-50/30 dark:bg-blue-900/10",
      accent: "text-blue-700 dark:text-blue-300",
      check: "text-blue-600 dark:text-blue-400",
      btn: "bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600",
    },
    green: {
      shell:
        "border-emerald-100/70 dark:border-emerald-900/50 bg-emerald-50/30 dark:bg-emerald-900/10",
      accent: "text-emerald-700 dark:text-emerald-300",
      check: "text-emerald-600 dark:text-emerald-400",
      btn: "bg-emerald-600 hover:bg-emerald-700 dark:bg-emerald-500 dark:hover:bg-emerald-600",
    },
    gray: {
      shell: "border-slate-200/70 dark:border-slate-800 bg-white/60 dark:bg-slate-900/30",
      accent: "text-slate-700 dark:text-slate-200",
      check: "text-slate-600 dark:text-slate-300",
      btn: "bg-slate-900 hover:bg-slate-800 dark:bg-slate-100 dark:hover:bg-white dark:text-slate-900",
    },
  };

  const t = themes[theme] || themes.gray;

  return (
    <div
      className={`group flex flex-col border rounded-2xl p-8 transition-all duration-300 hover:shadow-xl hover:-translate-y-1 ${t.shell}`}
    >
      <h3 className={`text-2xl font-bold mb-3 tracking-tight ${t.accent}`}>{title}</h3>
      <p className="text-slate-600 dark:text-slate-400 mb-6 leading-relaxed">
        {description}
      </p>
      
      <ul className="flex-grow space-y-3 mb-8">
        {features.map((item, index) => (
          <li key={index} className="flex items-start text-sm text-slate-600 dark:text-slate-400">
            <span className={`mr-2 mt-0.5 font-bold ${t.check}`}>✓</span>
            {item}
          </li>
        ))}
      </ul>

      <a
        href={href || "#"}
        className={`w-full text-center py-3 px-4 rounded-xl text-white font-semibold transition-all shadow-sm active:scale-[0.99] ${t.btn}`}
      >
        {buttonText}
      </a>
    </div>
  );
}
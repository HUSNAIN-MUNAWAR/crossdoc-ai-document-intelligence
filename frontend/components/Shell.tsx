import Link from "next/link";
import {
  Activity,
  BarChart3,
  FileSearch,
  Files,
  Gauge,
  LayoutDashboard,
  Scale,
  ShieldCheck,
  Upload,
} from "lucide-react";

const navigation = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/upload", label: "Process documents", icon: Upload },
  { href: "/cases", label: "Cases", icon: Files },
  { href: "/documents/1", label: "Document inspector", icon: FileSearch },
  { href: "/reconciliation", label: "Reconciliation", icon: Scale },
  { href: "/risk", label: "Risk analysis", icon: ShieldCheck },
  { href: "/review", label: "Review queue", icon: Gauge },
  { href: "/evaluation", label: "Evaluation", icon: BarChart3 },
  { href: "/system-health", label: "System health", icon: Activity },
];

export function Shell({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  return (
    <main className="min-h-screen min-w-0 overflow-x-hidden lg:pl-64">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-white/10 bg-[#0d1118] lg:flex lg:flex-col">
        <div className="border-b border-white/10 px-6 py-6">
          <Link href="/dashboard" className="flex items-center gap-3">
            <span className="grid h-9 w-9 place-items-center rounded-md bg-cyan-400 font-black text-slate-950">
              C
            </span>
            <span>
              <span className="block font-semibold">CrossDoc AI</span>
              <span className="block text-xs text-slate-500">Document intelligence</span>
            </span>
          </Link>
        </div>
        <nav className="flex-1 space-y-1 px-3 py-4">
          {navigation.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className="flex items-center gap-3 rounded-md px-3 py-2.5 text-sm text-slate-400 transition hover:bg-white/[.06] hover:text-white"
            >
              <Icon size={17} aria-hidden="true" />
              {label}
            </Link>
          ))}
        </nav>
        <div className="border-t border-white/10 p-4 text-xs leading-5 text-slate-500">
          Local-first OCR with explainable controls
        </div>
      </aside>

      <header className="border-b border-white/10 bg-[#0d1118] px-5 py-4 lg:hidden">
        <Link href="/dashboard" className="font-semibold">CrossDoc AI</Link>
        <nav className="mt-3 flex gap-4 overflow-x-auto text-sm text-slate-400">
          <Link href="/dashboard">Overview</Link>
          <Link href="/upload">Process</Link>
          <Link href="/system-health">Health</Link>
        </nav>
      </header>

      <section className="mx-auto min-w-0 max-w-[1440px] p-5 sm:p-7 lg:p-10">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase text-cyan-300">
              Document operations
            </p>
            <h1 className="mt-2 text-3xl font-semibold sm:text-4xl">{title}</h1>
            {subtitle && (
              <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400 sm:text-base">
                {subtitle}
              </p>
            )}
          </div>
          <Link href="/upload" className="btn">
            <Upload size={16} aria-hidden="true" />
            New case
          </Link>
        </div>
        <div className="mt-8">{children}</div>
      </section>
    </main>
  );
}

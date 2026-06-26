import Link from "next/link";
import { ArrowUpRight, CheckCircle2, Cpu, FileText, ScanLine } from "lucide-react";
import { Shell } from "@/components/Shell";
import { StatCard } from "@/components/StatCard";
import { RiskBadge } from "@/components/RiskBadge";
import { apiGet } from "@/lib/api";

type CaseRow = {
  case_id: string;
  title: string;
  status: string;
  risk_level: string;
  risk_score: number;
  average_confidence: number;
  document_count: number;
};

type OcrHealth = {
  tesseract?: { available: boolean; version?: string };
  paddleocr?: { available: boolean };
  opencv?: { available: boolean };
  demo_mode?: { enabled: boolean };
};

const fallbackCases: CaseRow[] = [
  { case_id: "SHIP-2026-001", title: "Jeddah shipment bundle", status: "needs_review", risk_level: "high", risk_score: 65, average_confidence: .83, document_count: 4 },
  { case_id: "SHIP-2026-002", title: "Riyadh shipment", status: "processed", risk_level: "low", risk_score: 14, average_confidence: .91, document_count: 3 },
];

export default async function Page() {
  const [cases, health] = await Promise.all([
    apiGet<CaseRow[]>("/api/cases", fallbackCases),
    apiGet<OcrHealth>("/api/system/ocr-health", {}),
  ]);
  const documentCount = cases.reduce((sum, item) => sum + item.document_count, 0);
  const confidence = cases.length
    ? cases.reduce((sum, item) => sum + item.average_confidence, 0) / cases.length
    : 0;
  const needsReview = cases.filter((item) => item.status.includes("review")).length;

  return (
    <Shell
      title="Operations overview"
      subtitle="Live case processing, OCR confidence, reconciliation risk, and engine readiness."
    >
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Active cases" value={String(cases.length)} hint="Persisted case workspaces" />
        <StatCard label="Documents" value={String(documentCount)} hint="PDF and image inputs" />
        <StatCard label="Needs review" value={String(needsReview)} hint="Human decision required" />
        <StatCard label="Avg OCR confidence" value={`${Math.round(confidence * 100)}%`} hint="Across processed cases" />
      </div>

      <div className="mt-6 grid min-w-0 gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
        <section className="min-w-0 overflow-hidden rounded-lg border border-white/10">
          <div className="flex items-center justify-between bg-[#121720] px-5 py-4">
            <div>
              <h2 className="font-semibold">Recent cases</h2>
              <p className="mt-1 text-xs text-slate-500">Persisted API data</p>
            </div>
            <Link href="/cases" className="text-sm text-cyan-300 hover:text-cyan-200">View all</Link>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-y border-white/10 bg-white/[.02] text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-5 py-3 font-medium">Case</th>
                  <th className="px-4 py-3 font-medium">Documents</th>
                  <th className="hidden px-4 py-3 font-medium sm:table-cell">Status</th>
                  <th className="hidden px-4 py-3 font-medium md:table-cell">Risk</th>
                  <th className="hidden px-4 py-3 font-medium lg:table-cell">Confidence</th>
                  <th className="hidden px-4 py-3 sm:table-cell"><span className="sr-only">Open</span></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/10 bg-[#0f141c]">
                {cases.map((item) => (
                  <tr key={item.case_id} className="hover:bg-white/[.025]">
                    <td className="px-5 py-4">
                      <div className="font-medium">{item.case_id}</div>
                      <div className="mt-1 text-xs text-slate-500">{item.title}</div>
                    </td>
                    <td className="px-4 py-4">{item.document_count}</td>
                    <td className="hidden px-4 py-4 capitalize text-slate-300 sm:table-cell">{item.status.replaceAll("_", " ")}</td>
                    <td className="hidden px-4 py-4 md:table-cell"><RiskBadge level={item.risk_level} /></td>
                    <td className="hidden px-4 py-4 lg:table-cell">{Math.round(item.average_confidence * 100)}%</td>
                    <td className="hidden px-4 py-4 sm:table-cell">
                      <Link href={`/cases/${item.case_id}`} aria-label={`Open ${item.case_id}`} className="text-slate-500 hover:text-white">
                        <ArrowUpRight size={17} />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <aside className="min-w-0 space-y-4">
          <div className="card p-5">
            <div className="flex items-center gap-3">
              <Cpu size={18} className="text-cyan-300" />
              <h2 className="font-semibold">OCR runtime</h2>
            </div>
            <div className="mt-5 space-y-4 text-sm">
              <HealthRow label="Tesseract" ready={Boolean(health.tesseract?.available)} />
              <HealthRow label="OpenCV" ready={Boolean(health.opencv?.available)} />
              <HealthRow label="PaddleOCR" ready={Boolean(health.paddleocr?.available)} optional />
              <HealthRow label="Demo fallback" ready={Boolean(health.demo_mode?.enabled)} disabledLabel="Disabled" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Link href="/upload" className="card p-4 transition hover:border-cyan-400/40">
              <ScanLine size={19} className="text-cyan-300" />
              <span className="mt-3 block text-sm font-medium">Run OCR</span>
            </Link>
            <Link href="/evaluation" className="card p-4 transition hover:border-emerald-400/40">
              <FileText size={19} className="text-emerald-300" />
              <span className="mt-3 block text-sm font-medium">Metrics</span>
            </Link>
          </div>
        </aside>
      </div>
    </Shell>
  );
}

function HealthRow({ label, ready, optional = false, disabledLabel = "Unavailable" }: { label: string; ready: boolean; optional?: boolean; disabledLabel?: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-slate-400">{label}</span>
      <span className={`inline-flex items-center gap-1.5 text-xs ${ready ? "text-emerald-300" : optional ? "text-amber-300" : "text-slate-500"}`}>
        {ready && <CheckCircle2 size={13} />}
        {ready ? "Ready" : optional ? "Optional" : disabledLabel}
      </span>
    </div>
  );
}

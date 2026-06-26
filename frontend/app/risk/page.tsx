import { Shell } from "@/components/Shell";
import { RiskBadge } from "@/components/RiskBadge";
import { apiGet } from "@/lib/api";

type CaseRow = { case_id: string };
type Factor = { type: string; points: number; explanation?: string; message?: string };
type Report = { score: number; level: string; factors: Factor[]; recommended_actions: string[] };

export default async function Page() {
  const cases = await apiGet<CaseRow[]>("/api/cases", []);
  const caseId = cases[0]?.case_id;
  const report = caseId
    ? await apiGet<Report>(`/api/cases/${encodeURIComponent(caseId)}/risk`, { score: 0, level: "unknown", factors: [], recommended_actions: [] })
    : { score: 0, level: "unknown", factors: [], recommended_actions: [] };

  return (
    <Shell title="Risk analysis" subtitle={`Explainable decision support${caseId ? ` for ${caseId}` : ""}.`}>
      <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
        <section className="card p-6">
          <div className="text-xs uppercase text-slate-500">Risk score</div>
          <div className="mt-4 text-6xl font-semibold">{report.score}</div>
          <div className="mt-4"><RiskBadge level={report.level} /></div>
          <div className="mt-6 border-t border-white/10 pt-5 text-sm text-slate-400">
            {report.recommended_actions?.[0] || "Process a case to calculate risk."}
          </div>
        </section>
        <section className="overflow-hidden rounded-lg border border-white/10 bg-[#0f141c]">
          <div className="border-b border-white/10 bg-[#121720] px-5 py-4"><h2 className="font-semibold">Risk factors</h2></div>
          <div className="divide-y divide-white/10">
            {report.factors?.map((factor, index) => (
              <div key={`${factor.type}-${index}`} className="grid gap-2 px-5 py-4 sm:grid-cols-[1fr_70px]">
                <div><div className="text-sm font-medium capitalize">{factor.type.replaceAll("_", " ")}</div><div className="mt-1 text-xs text-slate-500">{factor.explanation || factor.message}</div></div>
                <div className="text-sm font-semibold text-amber-300 sm:text-right">+{factor.points}</div>
              </div>
            ))}
            {!report.factors?.length && <p className="px-5 py-10 text-sm text-slate-500">No risk factors were triggered.</p>}
          </div>
        </section>
      </div>
    </Shell>
  );
}

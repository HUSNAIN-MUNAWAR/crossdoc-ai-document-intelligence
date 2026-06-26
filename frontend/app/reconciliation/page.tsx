import { CheckCircle2 } from "lucide-react";
import { Shell } from "@/components/Shell";
import { apiGet } from "@/lib/api";

type CaseRow = { case_id: string };
type Issue = {
  issue_type: string;
  severity: string;
  message: string;
  source_documents: string[];
  recommended_action: string;
};

export default async function Page() {
  const cases = await apiGet<CaseRow[]>("/api/cases", []);
  const caseId = cases[0]?.case_id;
  const issues = caseId
    ? await apiGet<Issue[]>(`/api/cases/${encodeURIComponent(caseId)}/reconciliation`, [])
    : [];

  return (
    <Shell title="Reconciliation" subtitle={`Cross-document consistency findings${caseId ? ` for ${caseId}` : ""}.`}>
      {issues.length ? (
        <div className="space-y-4">
          {issues.map((issue, index) => (
            <article key={`${issue.issue_type}-${index}`} className="card p-5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <h2 className="font-semibold capitalize">{issue.issue_type.replaceAll("_", " ")}</h2>
                <span className={`badge ${issue.severity === "high" ? "bg-red-400/10 text-red-200" : "bg-amber-400/10 text-amber-200"}`}>{issue.severity}</span>
              </div>
              <p className="mt-3 text-sm text-slate-300">{issue.message}</p>
              <p className="mt-3 text-xs text-slate-500">Sources: {issue.source_documents.join(", ")}</p>
              <p className="mt-4 border-t border-white/10 pt-4 text-sm text-cyan-200">{issue.recommended_action}</p>
            </article>
          ))}
        </div>
      ) : (
        <div className="card flex items-start gap-3 p-6">
          <CheckCircle2 className="mt-0.5 text-emerald-300" size={20} />
          <div><h2 className="font-semibold">No mismatches detected</h2><p className="mt-1 text-sm text-slate-500">The latest processed case has no persisted reconciliation issues.</p></div>
        </div>
      )}
    </Shell>
  );
}

import { Shell } from "@/components/Shell";
import { apiGet } from "@/lib/api";

type EvaluationRun = {
  id: number;
  name: string;
  report_path: string;
  metrics: Record<string, unknown>;
};

export default async function Page() {
  const runs = await apiGet<EvaluationRun[]>("/api/evaluation/runs", []);
  const run = runs[0];
  const metrics = Object.entries(run?.metrics || {}).filter(([, value]) => typeof value === "number");

  return (
    <Shell title="Evaluation" subtitle="Versioned synthetic regression metrics for extraction and decision logic.">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {metrics.map(([name, value]) => (
          <div key={name} className="card p-5">
            <div className="text-xs uppercase leading-5 text-slate-500">{name.replaceAll("_", " ")}</div>
            <div className="mt-3 text-3xl font-semibold">{formatMetric(name, value as number)}</div>
          </div>
        ))}
      </div>
      {!run && <div className="card p-6 text-sm text-slate-500">No evaluation report is available. Run the evaluation script first.</div>}
      {run && <p className="mt-5 text-xs text-slate-500">Source: {run.report_path}. Metrics use generated fixtures and are not universal OCR benchmarks.</p>}
    </Shell>
  );
}

function formatMetric(name: string, value: number) {
  if (name.includes("count")) return String(value);
  if (name.includes("seconds")) return `${value.toFixed(3)}s`;
  return `${Math.round(value * 100)}%`;
}

import { CheckCircle2 } from "lucide-react";
import { Shell } from "@/components/Shell";
import { apiGet } from "@/lib/api";

type Task = {
  id: number;
  document_id: number;
  field_name: string;
  original_value: string;
  suggested_value: string;
  confidence: number;
  reason: string;
  status: string;
};

export default async function Page() {
  const tasks = await apiGet<Task[]>("/api/review/tasks", []);
  return (
    <Shell title="Review queue" subtitle="Persisted low-confidence fields awaiting a human decision.">
      {tasks.length ? (
        <div className="overflow-hidden rounded-lg border border-white/10 bg-[#0f141c]">
          <div className="divide-y divide-white/10">
            {tasks.map((task) => (
              <article key={task.id} className="grid gap-4 px-5 py-5 md:grid-cols-[180px_1fr_100px] md:items-center">
                <div><div className="text-xs uppercase text-slate-500">{task.field_name.replaceAll("_", " ")}</div><div className="mt-2 text-sm">{task.suggested_value || task.original_value}</div></div>
                <div><div className="text-sm text-slate-300">{task.reason}</div><div className="mt-2 text-xs text-slate-500">Document {task.document_id} | {task.status}</div></div>
                <div className="text-sm font-semibold text-amber-300 md:text-right">{Math.round(task.confidence * 100)}%</div>
              </article>
            ))}
          </div>
        </div>
      ) : (
        <div className="card flex items-start gap-3 p-6">
          <CheckCircle2 className="mt-0.5 text-emerald-300" size={20} />
          <div><h2 className="font-semibold">Review queue is clear</h2><p className="mt-1 text-sm text-slate-500">No persisted fields are below the configured confidence threshold.</p></div>
        </div>
      )}
    </Shell>
  );
}

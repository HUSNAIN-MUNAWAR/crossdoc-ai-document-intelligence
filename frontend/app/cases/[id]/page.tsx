import Link from "next/link";
import { FileSearch } from "lucide-react";
import { Shell } from "@/components/Shell";
import { RiskBadge } from "@/components/RiskBadge";
import { apiGet } from "@/lib/api";

type Document = {
  id: number;
  filename: string;
  document_type: string;
  status: string;
  quality_score: number;
  ocr_confidence: number;
};

type CaseDetail = {
  case_id: string;
  title: string;
  status: string;
  risk_level: string;
  risk_score: number;
  average_confidence: number;
  documents: Document[];
};

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const caseId = decodeURIComponent(id);
  const detail = await apiGet<CaseDetail>(`/api/cases/${encodeURIComponent(caseId)}`, {
    case_id: caseId,
    title: "Case not found",
    status: "unavailable",
    risk_level: "unknown",
    risk_score: 0,
    average_confidence: 0,
    documents: [],
  });

  return (
    <Shell title={detail.case_id} subtitle={detail.title}>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Metric label="Status" value={detail.status.replaceAll("_", " ")} />
        <Metric label="Documents" value={String(detail.documents.length)} />
        <Metric label="OCR confidence" value={`${Math.round(detail.average_confidence * 100)}%`} />
        <div className="card p-5">
          <div className="text-xs uppercase text-slate-500">Risk score</div>
          <div className="mt-3 flex items-center gap-3 text-2xl font-semibold">
            {detail.risk_score}<RiskBadge level={detail.risk_level} />
          </div>
        </div>
      </div>

      <section className="mt-6 overflow-hidden rounded-lg border border-white/10 bg-[#0f141c]">
        <div className="border-b border-white/10 bg-[#121720] px-5 py-4">
          <h2 className="font-semibold">Source documents</h2>
        </div>
        <div className="divide-y divide-white/10">
          {detail.documents.map((document) => (
            <div key={document.id} className="flex flex-wrap items-center justify-between gap-4 px-5 py-4">
              <div className="min-w-0">
                <div className="truncate text-sm font-medium">{document.filename}</div>
                <div className="mt-1 text-xs capitalize text-slate-500">
                  {document.document_type.replaceAll("_", " ")} | {document.status} | {Math.round(document.ocr_confidence * 100)}%
                </div>
              </div>
              <Link href={`/documents/${document.id}`} className="btn-secondary">
                <FileSearch size={16} /> Inspect
              </Link>
            </div>
          ))}
          {!detail.documents.length && <p className="px-5 py-10 text-sm text-slate-500">No documents are attached.</p>}
        </div>
      </section>
    </Shell>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div className="card p-5"><div className="text-xs uppercase text-slate-500">{label}</div><div className="mt-3 text-2xl font-semibold capitalize">{value}</div></div>;
}

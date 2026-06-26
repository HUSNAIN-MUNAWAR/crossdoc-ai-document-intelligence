import { Shell } from "@/components/Shell";
import { apiGet } from "@/lib/api";

type DocumentResult = {
  id: number;
  filename: string;
  document_type: string;
  status: string;
  quality_score: number;
  ocr_confidence: number;
  page_count: number;
  ocr_block_count: number;
  fields: Record<string, { raw_value: unknown; normalized_value: unknown; confidence: number }>;
};

type OcrBlock = {
  text: string;
  normalized_text: string;
  confidence: number;
  engine_name: string;
  page_number: number;
};

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const [document, blocks] = await Promise.all([
    apiGet<DocumentResult>(`/api/documents/${id}`, {
      id: Number(id),
      filename: "No processed document found",
      document_type: "unknown",
      status: "unavailable",
      quality_score: 0,
      ocr_confidence: 0,
      page_count: 0,
      ocr_block_count: 0,
      fields: {},
    }),
    apiGet<OcrBlock[]>(`/api/documents/${id}/ocr`, []),
  ]);

  const fields = Object.entries(document.fields || {}).filter(([name]) => name !== "line_items");
  const engine = blocks[0]?.engine_name ?? "not available";

  return (
    <Shell
      title="Document inspector"
      subtitle="Persisted OCR evidence and normalized field extraction for a processed source document."
    >
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <Metric label="Document" value={document.filename} />
        <Metric label="Type" value={document.document_type.replaceAll("_", " ")} />
        <Metric label="OCR engine" value={engine} />
        <Metric label="OCR confidence" value={`${Math.round(document.ocr_confidence * 100)}%`} />
        <Metric label="Text blocks" value={String(document.ocr_block_count)} />
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-2">
        <section className="overflow-hidden rounded-lg border border-white/10 bg-[#0f141c]">
          <div className="border-b border-white/10 px-5 py-4">
            <h2 className="font-semibold">Extracted fields</h2>
            <p className="mt-1 text-xs text-slate-500">Raw OCR value, normalized value, and confidence</p>
          </div>
          <div className="divide-y divide-white/10">
            {fields.length ? fields.map(([name, field]) => (
              <div key={name} className="grid gap-2 px-5 py-4 sm:grid-cols-[150px_1fr_64px] sm:items-center">
                <span className="text-xs uppercase text-slate-500">{name.replaceAll("_", " ")}</span>
                <span className="text-sm">{String(field.normalized_value ?? field.raw_value ?? "")}</span>
                <span className="text-xs text-emerald-300 sm:text-right">{Math.round(field.confidence * 100)}%</span>
              </div>
            )) : <p className="px-5 py-8 text-sm text-slate-500">No extracted fields are available.</p>}
          </div>
        </section>

        <section className="overflow-hidden rounded-lg border border-white/10 bg-[#0f141c]">
          <div className="border-b border-white/10 px-5 py-4">
            <h2 className="font-semibold">OCR evidence</h2>
            <p className="mt-1 text-xs text-slate-500">Text returned by the selected engine</p>
          </div>
          <div className="max-h-[620px] divide-y divide-white/10 overflow-y-auto">
            {blocks.length ? blocks.map((block, index) => (
              <div key={`${block.page_number}-${index}`} className="grid grid-cols-[1fr_64px] gap-4 px-5 py-3 text-sm">
                <span>{block.text}</span>
                <span className={`text-right text-xs ${block.confidence >= .75 ? "text-emerald-300" : "text-amber-300"}`}>
                  {Math.round(block.confidence * 100)}%
                </span>
              </div>
            )) : <p className="px-5 py-8 text-sm text-slate-500">No OCR blocks are available.</p>}
          </div>
        </section>
      </div>
    </Shell>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="card min-w-0 p-4">
      <div className="text-xs uppercase text-slate-500">{label}</div>
      <div className="mt-2 truncate text-sm font-semibold capitalize" title={value}>{value}</div>
    </div>
  );
}

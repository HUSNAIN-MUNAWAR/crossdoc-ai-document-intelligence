"use client";

import { FormEvent, useMemo, useState } from "react";
import Link from "next/link";
import { CheckCircle2, FileUp, LoaderCircle, ScanLine } from "lucide-react";
import { Shell } from "@/components/Shell";
import { API_BASE } from "@/lib/api";

type ProcessedDocument = {
  id: number;
  filename: string;
  document_type: string;
  ocr_confidence: number;
  ocr_block_count: number;
};

type ProcessResult = {
  case_id: string;
  status: string;
  documents: ProcessedDocument[];
  reconciliation_issues: unknown[];
  risk: { score: number; level: string };
};

function defaultCaseId() {
  const timestamp = new Date().toISOString().replace(/\D/g, "").slice(0, 14);
  return `CASE-${timestamp}`;
}

export default function Page() {
  const initialId = useMemo(defaultCaseId, []);
  const [caseId, setCaseId] = useState(initialId);
  const [title, setTitle] = useState("Document intelligence review");
  const [files, setFiles] = useState<File[]>([]);
  const [status, setStatus] = useState<"idle" | "submitting" | "done" | "error">("idle");
  const [message, setMessage] = useState("");
  const [result, setResult] = useState<ProcessResult | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!files.length) {
      setStatus("error");
      setMessage("Select at least one PDF or image.");
      return;
    }

    setStatus("submitting");
    setMessage("Creating case and uploading source documents...");
    setResult(null);

    try {
      const create = await fetch(`${API_BASE}/api/cases`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ case_id: caseId, title }),
      });
      if (!create.ok) throw new Error(await responseError(create));

      const form = new FormData();
      files.forEach((file) => form.append("files", file));
      const upload = await fetch(`${API_BASE}/api/cases/${encodeURIComponent(caseId)}/documents`, {
        method: "POST",
        body: form,
      });
      if (!upload.ok) throw new Error(await responseError(upload));

      setMessage("Running preprocessing, OCR, extraction, reconciliation, and risk scoring...");
      const process = await fetch(`${API_BASE}/api/cases/${encodeURIComponent(caseId)}/process`, {
        method: "POST",
      });
      if (!process.ok) throw new Error(await responseError(process));

      const payload = await process.json() as ProcessResult;
      setResult(payload);
      setStatus("done");
      setMessage(`Processed ${payload.documents.length} document${payload.documents.length === 1 ? "" : "s"} successfully.`);
    } catch (error) {
      setStatus("error");
      setMessage(error instanceof Error ? error.message : "Processing failed.");
    }
  }

  return (
    <Shell
      title="Process document bundle"
      subtitle="Create a case, upload business documents, and execute the real local OCR pipeline."
    >
      <div className="grid gap-6 xl:grid-cols-[minmax(0,720px)_minmax(300px,1fr)]">
        <form onSubmit={submit} className="card p-5 sm:p-6">
          <div className="grid gap-5 sm:grid-cols-2">
            <label className="block text-sm text-slate-300">
              Case ID
              <input className="field mt-2" value={caseId} onChange={(event) => setCaseId(event.target.value)} required />
            </label>
            <label className="block text-sm text-slate-300">
              Case title
              <input className="field mt-2" value={title} onChange={(event) => setTitle(event.target.value)} required />
            </label>
          </div>

          <label className="mt-6 grid min-h-52 cursor-pointer place-items-center rounded-lg border border-dashed border-white/20 bg-black/10 p-6 text-center transition hover:border-cyan-400/50 hover:bg-cyan-400/[.03]">
            <input
              className="sr-only"
              type="file"
              accept=".pdf,.png,.jpg,.jpeg,.tif,.tiff"
              multiple
              onChange={(event) => setFiles(Array.from(event.target.files ?? []))}
            />
            <span>
              <FileUp className="mx-auto text-cyan-300" size={28} />
              <span className="mt-4 block font-medium">Choose PDFs or scanned images</span>
              <span className="mt-2 block text-sm text-slate-500">
                {files.length ? `${files.length} file${files.length === 1 ? "" : "s"} selected` : "Invoice, packing list, bill of lading, PO, receipt, or payment proof"}
              </span>
            </span>
          </label>

          {files.length > 0 && (
            <div className="mt-4 divide-y divide-white/10 rounded-lg border border-white/10">
              {files.map((file) => (
                <div key={`${file.name}-${file.size}`} className="flex items-center justify-between px-4 py-3 text-sm">
                  <span className="truncate pr-4">{file.name}</span>
                  <span className="shrink-0 text-xs text-slate-500">{Math.max(1, Math.round(file.size / 1024))} KB</span>
                </div>
              ))}
            </div>
          )}

          <button className="btn mt-6 w-full sm:w-auto" type="submit" disabled={status === "submitting"}>
            {status === "submitting" ? <LoaderCircle className="animate-spin" size={17} /> : <ScanLine size={17} />}
            {status === "submitting" ? "Processing" : "Run document intelligence"}
          </button>
        </form>

        <section className="space-y-4">
          <div className="card p-5">
            <h2 className="font-semibold">Pipeline status</h2>
            <div className={`mt-4 rounded-md border px-4 py-3 text-sm ${status === "error" ? "border-red-400/30 bg-red-400/10 text-red-200" : status === "done" ? "border-emerald-400/30 bg-emerald-400/10 text-emerald-200" : "border-white/10 bg-white/[.025] text-slate-400"}`}>
              <span className="flex items-start gap-2">
                {status === "done" && <CheckCircle2 className="mt-0.5 shrink-0" size={16} />}
                {message || "Waiting for a document bundle."}
              </span>
            </div>
          </div>

          {result && (
            <div className="card p-5">
              <div className="flex items-center justify-between">
                <h2 className="font-semibold">Processing result</h2>
                <span className="badge bg-cyan-400/10 text-cyan-200">{result.risk.level} risk</span>
              </div>
              <dl className="mt-5 grid grid-cols-2 gap-4 text-sm">
                <div><dt className="text-slate-500">Risk score</dt><dd className="mt-1 text-xl font-semibold">{result.risk.score}</dd></div>
                <div><dt className="text-slate-500">Issues</dt><dd className="mt-1 text-xl font-semibold">{result.reconciliation_issues.length}</dd></div>
              </dl>
              <div className="mt-5 space-y-3">
                {result.documents.map((document) => (
                  <Link key={document.id} href={`/documents/${document.id}`} className="block rounded-md border border-white/10 p-4 transition hover:border-cyan-400/40">
                    <span className="block truncate text-sm font-medium">{document.filename}</span>
                    <span className="mt-2 block text-xs text-slate-500">
                      {document.document_type.replaceAll("_", " ")} | {document.ocr_block_count} OCR blocks | {Math.round(document.ocr_confidence * 100)}%
                    </span>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </section>
      </div>
    </Shell>
  );
}

async function responseError(response: Response) {
  try {
    const payload = await response.json() as { detail?: string };
    return payload.detail || `Request failed (${response.status})`;
  } catch {
    return `Request failed (${response.status})`;
  }
}

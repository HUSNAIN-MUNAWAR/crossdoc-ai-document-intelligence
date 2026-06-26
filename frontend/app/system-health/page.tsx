import { CheckCircle2, CircleOff } from "lucide-react";
import { Shell } from "@/components/Shell";
import { apiGet } from "@/lib/api";

type Engine = { available: boolean; status: string; version?: string | null };
type Health = {
  paddleocr?: Engine;
  tesseract?: Engine;
  docling?: Engine;
  layoutparser?: Engine;
  poppler?: Engine;
  opencv?: Engine;
  demo_mode?: { enabled: boolean };
  language?: string;
};

export default async function Page() {
  const health = await apiGet<Health>("/api/system/ocr-health", {});
  const engines = [
    ["Tesseract OCR", health.tesseract],
    ["OpenCV", health.opencv],
    ["Poppler", health.poppler],
    ["PaddleOCR", health.paddleocr],
    ["Docling", health.docling],
    ["LayoutParser", health.layoutparser],
  ] as const;

  return (
    <Shell title="System health" subtitle="Runtime discovery for OCR, PDF rendering, preprocessing, and optional document AI adapters.">
      <div className="overflow-hidden rounded-lg border border-white/10 bg-[#0f141c]">
        <div className="grid grid-cols-[1fr_100px] gap-4 border-b border-white/10 bg-[#121720] px-5 py-3 text-xs uppercase text-slate-500 sm:grid-cols-[1fr_130px_1fr]">
          <span>Component</span><span>Status</span><span className="hidden sm:block">Version</span>
        </div>
        {engines.map(([name, engine]) => (
          <div key={name} className="grid grid-cols-[1fr_100px] gap-4 border-b border-white/10 px-5 py-4 text-sm last:border-0 sm:grid-cols-[1fr_130px_1fr]">
            <span className="font-medium">{name}</span>
            <span className={`inline-flex items-center gap-2 text-xs ${engine?.available ? "text-emerald-300" : "text-slate-500"}`}>
              {engine?.available ? <CheckCircle2 size={14} /> : <CircleOff size={14} />}
              {engine?.available ? "Ready" : "Optional"}
            </span>
            <span className="hidden truncate text-slate-500 sm:block">{engine?.version || engine?.status || "Not installed"}</span>
          </div>
        ))}
      </div>
      <div className="mt-5 flex flex-wrap gap-3 text-xs">
        <span className="badge bg-cyan-400/10 text-cyan-200">Language: {health.language || "en"}</span>
        <span className={`badge ${health.demo_mode?.enabled ? "bg-amber-400/10 text-amber-200" : "bg-emerald-400/10 text-emerald-200"}`}>
          Demo OCR: {health.demo_mode?.enabled ? "enabled" : "disabled"}
        </span>
      </div>
    </Shell>
  );
}

import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { Shell } from "@/components/Shell";
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

export default async function Page() {
  const cases = await apiGet<CaseRow[]>("/api/cases", []);
  return (
    <Shell title="Cases" subtitle="Persisted document bundles and their latest processing decisions.">
      <div className="overflow-hidden rounded-lg border border-white/10 bg-[#0f141c]">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-white/10 bg-[#121720] text-xs uppercase text-slate-500">
              <tr>
                <th className="px-5 py-3 font-medium">Case</th>
                <th className="px-4 py-3 font-medium">Documents</th>
                <th className="hidden px-4 py-3 font-medium sm:table-cell">Status</th>
                <th className="hidden px-4 py-3 font-medium md:table-cell">Risk</th>
                <th className="hidden px-4 py-3 font-medium lg:table-cell">Confidence</th>
                <th className="px-4 py-3"><span className="sr-only">Open</span></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/10">
              {cases.map((item) => (
                <tr key={item.case_id}>
                  <td className="px-5 py-4">
                    <div className="font-medium">{item.case_id}</div>
                    <div className="mt-1 text-xs text-slate-500">{item.title}</div>
                  </td>
                  <td className="px-4 py-4">{item.document_count}</td>
                  <td className="hidden px-4 py-4 capitalize text-slate-300 sm:table-cell">{item.status.replaceAll("_", " ")}</td>
                  <td className="hidden px-4 py-4 md:table-cell"><RiskBadge level={item.risk_level} /></td>
                  <td className="hidden px-4 py-4 lg:table-cell">{Math.round(item.average_confidence * 100)}%</td>
                  <td className="px-4 py-4">
                    <Link href={`/cases/${item.case_id}`} aria-label={`Open ${item.case_id}`} className="text-slate-500 hover:text-cyan-300">
                      <ArrowUpRight size={17} />
                    </Link>
                  </td>
                </tr>
              ))}
              {!cases.length && (
                <tr><td colSpan={6} className="px-5 py-12 text-center text-slate-500">No cases have been created.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </Shell>
  );
}

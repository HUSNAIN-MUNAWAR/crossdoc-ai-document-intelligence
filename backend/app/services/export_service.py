from io import StringIO, BytesIO
import csv, json, pandas as pd
class ExportService:
    def fields_csv(self, documents):
        b=StringIO(); w=csv.DictWriter(b, fieldnames=["document_type","field_name","raw_value","normalized_value","confidence"]); w.writeheader()
        for d in documents:
            for k,v in d.get("fields",{}).items():
                w.writerow({"document_type":d.get("document_type"),"field_name":k,"raw_value":v.get("raw_value"),"normalized_value":v.get("normalized_value"),"confidence":v.get("confidence")})
        return b.getvalue()
    def line_items_excel(self, documents):
        rows=[{"document_type":d.get("document_type"),"table_row":json.dumps(t)} for d in documents for t in d.get("tables",[])] or [{"document_type":"none","table_row":"no line items"}]
        out=BytesIO()
        with pd.ExcelWriter(out, engine="openpyxl") as wr: pd.DataFrame(rows).to_excel(wr,index=False,sheet_name="line_items")
        return out.getvalue()

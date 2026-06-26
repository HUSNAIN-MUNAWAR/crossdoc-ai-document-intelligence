class ReviewService:
    def create_tasks_for_fields(self, case_id, document_id, fields, threshold=.75):
        return [{"case_id":case_id,"document_id":document_id,"field_name":k,"original_value":v.get("raw_value",""),"suggested_value":v.get("normalized_value",""),"confidence":v.get("confidence",0),"reason":"Field confidence is below review threshold.","status":"open"} for k,v in fields.items() if isinstance(v,dict) and float(v.get("confidence",0))<threshold]
    def apply_correction(self, field_payload, corrected_value, reviewer_note=""):
        x=dict(field_payload); x.update({"corrected_value":corrected_value,"normalized_value":corrected_value,"reviewer_note":reviewer_note,"confidence":max(float(x.get("confidence",0)),.95),"review_status":"corrected"}); return x

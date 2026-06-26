from app.services.evaluation_service import EvaluationService

def test_evaluation_metrics_and_report(tmp_path):
    gt = [{"case_id":"C1","documents":[{"type":"commercial_invoice","fields":{"total_amount":100,"quantity":2}}]}]
    pred = [{"case_id":"C1","documents":[{"document_type":"commercial_invoice","fields":{"total_amount":{"raw_value":100,"normalized_value":100,"confidence":.9},"quantity":{"raw_value":2,"normalized_value":2,"confidence":.8}},"tables":[{"rows":[{"cells":["a"]}]}]}],"reconciliation_issues":[{"type":"amount_mismatch"}]}]
    service = EvaluationService(); metrics = service.evaluate(pred, gt, {"demo_mode":{"enabled":False}})
    assert metrics["document_classification_accuracy"] == 1
    paths = service.write_report(metrics, tmp_path)
    assert paths["json"].endswith("evaluation_report.json") and paths["csv"].endswith("evaluation_summary.csv")

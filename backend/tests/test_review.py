from app.services.review_service import ReviewService
def test_review_correction():
    out=ReviewService().apply_correction({"raw_value":"48O","normalized_value":"480","confidence":.7},"480","Looks correct")
    assert out["normalized_value"]=="480" and out["confidence"]>=.95

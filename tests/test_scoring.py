from app.scoring import compute_score

def test_high_on_time_high_compliance_low_complaints():
    score = compute_score(
        on_time_delivery_rate=95.0,
        complaint_count=0,
        missing_documents=False,
        compliance_score=90.0,
        category="supplier"
    )
    assert 0 <= score <= 100
    assert score >= 70

def test_missing_documents_penalty():
    s_without = compute_score(90, 0, False, 90, "supplier")
    s_with = compute_score(90, 0, True, 90, "supplier")
    assert s_with < s_without

def test_many_complaints_lower_score():
    s0 = compute_score(80, 0, False, 80, "dealer")
    s20 = compute_score(80, 20, False, 80, "dealer")
    assert s20 < s0

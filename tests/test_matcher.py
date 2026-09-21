from job_tracker.matcher import score_match


def test_score_identical_text_high():
    text = "Python Flask SQL Docker REST APIs software development"
    result = score_match(text, text)
    assert result["score"] == 100
    assert result["missing_terms"] == []


def test_finds_missing_skills():
    result = score_match("Build Python services with Flask, PostgreSQL, Docker, and AWS.", "Built Python APIs using Flask and PostgreSQL.")
    assert "Docker" in result["missing_terms"]
    assert "AWS" in result["missing_terms"]
    assert "Python" in result["matched_skills"]


def test_matcher_endpoint(client):
    response = client.post("/matcher", json={"job_description": "Python and SQL", "resume": "Python developer"})
    assert response.status_code == 200
    assert 0 <= response.json["score"] <= 100


def test_matcher_requires_both_texts(client):
    assert client.post("/matcher", json={"job_description": "Python"}).status_code == 400

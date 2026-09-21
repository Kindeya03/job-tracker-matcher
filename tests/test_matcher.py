from io import BytesIO

from job_tracker.matcher import score_match


def test_score_identical_text_high():
    text = ("Built Python Flask SQL Docker REST APIs software development for 500 users. " * 20)
    result = score_match(text, text)
    assert result["score"] >= 85
    assert result["missing_terms"] == []
    assert result["ranking"] == "Highly aligned"


def test_finds_missing_skills():
    result = score_match("Build Python services with Flask, PostgreSQL, Docker, and AWS.", "Built Python APIs using Flask and PostgreSQL.")
    assert "Docker" in result["missing_terms"]
    assert "AWS" in result["missing_terms"]
    assert "Python" in result["matched_skills"]


def test_matcher_endpoint(client):
    response = client.post("/matcher", json={"job_description": "Python and SQL", "resume": "Python developer"})
    assert response.status_code == 200
    assert 0 <= response.json["score"] <= 100
    assert "feedback" in response.json


def test_matcher_requires_both_texts(client):
    assert client.post("/matcher", json={"job_description": "Python"}).status_code == 400


def test_matcher_accepts_resume_upload(client):
    response = client.post(
        "/matcher",
        data={
            "job_description": "Python Flask AWS engineering role",
            "resume_file": (BytesIO(b"Built Python and Flask APIs for 200 users"), "resume.txt"),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    assert "Python" in response.json["matched_skills"]


def test_matcher_rejects_unsupported_upload(client):
    response = client.post(
        "/matcher",
        data={
            "job_description": "Python role",
            "resume_file": (BytesIO(b"resume"), "resume.exe"),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    assert "PDF, DOCX, or TXT" in response.json["error"]


def test_matcher_uses_job_url(client, monkeypatch):
    monkeypatch.setattr(
        "job_tracker.routes.extract_job_url",
        lambda _url: "Python Flask Docker software engineering position",
    )
    response = client.post(
        "/matcher",
        data={"job_url": "https://example.com/job", "resume": "Built Python Flask services"},
    )
    assert response.status_code == 200
    assert response.json["job_source"] == "url"

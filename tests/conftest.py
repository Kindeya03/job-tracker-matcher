import pytest

from job_tracker import create_app


@pytest.fixture()
def app(tmp_path):
    return create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.sqlite")})


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def sample_application():
    return {
        "company": "Acme",
        "role": "Software Engineer",
        "job_link": "https://example.com/job",
        "status": "Applied",
        "date_applied": "2026-09-20",
        "notes": "Follow up next week",
    }

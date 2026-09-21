from job_tracker.db import get_db


def test_create_edit_and_delete_application(app, client, sample_application):
    response = client.post("/applications/new", data=sample_application)
    assert response.status_code == 302
    with app.app_context():
        application = get_db().execute("SELECT * FROM applications").fetchone()
        application_id = application["id"]
        assert application["company"] == "Acme"
    response = client.post(
        f"/applications/{application_id}/edit",
        data={**sample_application, "status": "Interviewing"},
    )
    assert response.status_code == 302
    assert b"Interviewing" in client.get("/applications").data
    response = client.post(f"/applications/{application_id}/delete")
    assert response.status_code == 302
    with app.app_context():
        assert get_db().execute("SELECT COUNT(*) FROM applications").fetchone()[0] == 0


def test_rejects_invalid_application(client, sample_application):
    response = client.post(
        "/applications/new", data={**sample_application, "company": "", "status": "Unknown"}
    )
    assert response.status_code == 200
    assert b"Company is required" in response.data
    assert b"Choose a valid status" in response.data


def test_dashboard(client, sample_application):
    client.post("/applications/new", data=sample_application)
    response = client.get("/")
    assert response.status_code == 200
    assert b"Acme" in response.data

from datetime import date

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for

from .db import get_db
from .matcher import extract_document, extract_job_url, score_match

bp = Blueprint("main", __name__)
STATUSES = ("Applied", "Interviewing", "Offer", "Rejected")


def _application_or_404(application_id):
    application = get_db().execute(
        "SELECT * FROM applications WHERE id = ?", (application_id,)
    ).fetchone()
    if application is None:
        abort(404)
    return application


def _form_values():
    return {
        "company": request.form.get("company", "").strip(),
        "role": request.form.get("role", "").strip(),
        "job_link": request.form.get("job_link", "").strip(),
        "status": request.form.get("status", "Applied"),
        "date_applied": request.form.get("date_applied", ""),
        "notes": request.form.get("notes", "").strip(),
    }


def _validate(values):
    errors = []
    if not values["company"]:
        errors.append("Company is required.")
    if not values["role"]:
        errors.append("Role is required.")
    if values["status"] not in STATUSES:
        errors.append("Choose a valid status.")
    try:
        date.fromisoformat(values["date_applied"])
    except ValueError:
        errors.append("Choose a valid application date.")
    if values["job_link"] and not values["job_link"].startswith(("http://", "https://")):
        errors.append("Job link must start with http:// or https://.")
    return errors


@bp.get("/")
def dashboard():
    db = get_db()
    counts = {status: 0 for status in STATUSES}
    counts.update(
        {row["status"]: row["count"] for row in db.execute(
            "SELECT status, COUNT(*) AS count FROM applications GROUP BY status"
        )}
    )
    timeline = db.execute(
        """SELECT date_applied AS date, COUNT(*) AS count
           FROM applications GROUP BY date_applied ORDER BY date_applied"""
    ).fetchall()
    recent = db.execute(
        "SELECT * FROM applications ORDER BY date_applied DESC, id DESC LIMIT 5"
    ).fetchall()
    return render_template(
        "dashboard.html", counts=counts, total=sum(counts.values()), timeline=timeline, recent=recent
    )


@bp.get("/applications")
def applications():
    selected = request.args.get("status", "")
    db = get_db()
    if selected in STATUSES:
        rows = db.execute(
            "SELECT * FROM applications WHERE status = ? ORDER BY date_applied DESC, id DESC",
            (selected,),
        ).fetchall()
    else:
        selected = ""
        rows = db.execute(
            "SELECT * FROM applications ORDER BY date_applied DESC, id DESC"
        ).fetchall()
    return render_template("applications.html", applications=rows, selected=selected)


@bp.route("/applications/new", methods=("GET", "POST"))
def application_new():
    values = {"status": "Applied", "date_applied": date.today().isoformat()}
    if request.method == "POST":
        values = _form_values()
        errors = _validate(values)
        if not errors:
            db = get_db()
            db.execute(
                """INSERT INTO applications
                   (company, role, job_link, status, date_applied, notes)
                   VALUES (:company, :role, :job_link, :status, :date_applied, :notes)""",
                values,
            )
            db.commit()
            flash("Application added.", "success")
            return redirect(url_for("main.applications"))
        for error in errors:
            flash(error, "error")
    return render_template("application_form.html", application=values, title="Add application")


@bp.route("/applications/<int:application_id>/edit", methods=("GET", "POST"))
def application_edit(application_id):
    application = _application_or_404(application_id)
    values = application
    if request.method == "POST":
        values = _form_values()
        errors = _validate(values)
        if not errors:
            db = get_db()
            db.execute(
                """UPDATE applications SET company=:company, role=:role, job_link=:job_link,
                   status=:status, date_applied=:date_applied, notes=:notes,
                   updated_at=CURRENT_TIMESTAMP WHERE id=:id""",
                {**values, "id": application_id},
            )
            db.commit()
            flash("Application updated.", "success")
            return redirect(url_for("main.applications"))
        for error in errors:
            flash(error, "error")
    return render_template("application_form.html", application=values, title="Edit application")


@bp.post("/applications/<int:application_id>/delete")
def application_delete(application_id):
    _application_or_404(application_id)
    db = get_db()
    db.execute("DELETE FROM applications WHERE id = ?", (application_id,))
    db.commit()
    flash("Application deleted.", "success")
    return redirect(url_for("main.applications"))


@bp.route("/matcher", methods=("GET", "POST"))
def matcher():
    if request.method == "GET":
        return render_template("matcher.html")
    payload = request.get_json(silent=True) or request.form
    job_description = str(payload.get("job_description", "")).strip()
    job_url = str(payload.get("job_url", "")).strip()
    resume = str(payload.get("resume", "")).strip()
    cover_letter = str(payload.get("cover_letter", "")).strip()
    try:
        resume = extract_document(request.files.get("resume_file")) or resume
        cover_letter = extract_document(request.files.get("cover_letter_file")) or cover_letter
        job_description = extract_job_url(job_url) or job_description
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    if not job_description or not resume:
        return jsonify({"error": "Add a job description or public job link, plus your resume."}), 400
    result = score_match(job_description, resume, cover_letter)
    result["job_source"] = "url" if job_url else "pasted text"
    return jsonify(result)


@bp.get("/health")
def health():
    return {"status": "ok"}


@bp.app_context_processor
def template_globals():
    return {"statuses": STATUSES}

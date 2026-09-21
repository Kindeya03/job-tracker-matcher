import os
from datetime import date, timedelta

from flask import Flask

from .db import close_db, init_db


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
        DATABASE=os.path.join(app.instance_path, "job_tracker.sqlite"),
    )

    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    app.teardown_appcontext(close_db)

    from .routes import bp

    app.register_blueprint(bp)

    with app.app_context():
        init_db()

    @app.cli.command("seed")
    def seed():
        """Add realistic sample applications for a quick product demo."""
        from .db import get_db

        db = get_db()
        if db.execute("SELECT COUNT(*) FROM applications").fetchone()[0]:
            print("Skipped: the database already contains applications.")
            return
        today = date.today()
        rows = [
            ("Stripe", "Software Engineering Intern", "Interviewing", today - timedelta(days=2), "Technical interview next Tuesday."),
            ("Notion", "Backend Engineering Intern", "Applied", today - timedelta(days=5), "Applied through university portal."),
            ("Figma", "Product Engineering Intern", "Applied", today - timedelta(days=8), "Referral submitted."),
            ("Vercel", "Developer Experience Intern", "Rejected", today - timedelta(days=14), "Revisit after more TypeScript work."),
            ("Linear", "Software Engineer Intern", "Offer", today - timedelta(days=21), "Offer deadline Friday."),
        ]
        db.executemany(
            "INSERT INTO applications (company, role, status, date_applied, notes) VALUES (?, ?, ?, ?, ?)",
            [(company, role, status, applied.isoformat(), notes) for company, role, status, applied, notes in rows],
        )
        db.commit()
        print("Added 5 sample applications.")

    return app

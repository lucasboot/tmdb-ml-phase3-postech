from flask import Blueprint, render_template, current_app

dash_bp = Blueprint("dash", __name__)


@dash_bp.get("/")
def index():
    return render_template("index.html", poll_ms=current_app.config.get("POLL_INTERVAL_MS", 30000))


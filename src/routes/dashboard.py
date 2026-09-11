from flask import Blueprint, render_template

from src.repositories import analytics_repo

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def index():
    return render_template("dashboard.html", stats=analytics_repo.dashboard())

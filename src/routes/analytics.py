from flask import Blueprint, render_template

from src.repositories import analytics_repo

analytics_bp = Blueprint("analytics", __name__, url_prefix="/analytics")


@analytics_bp.route("/")
def index():
    above_average, average = analytics_repo.above_average_occupancy()
    return render_template(
        "analytics.html",
        by_category=analytics_repo.by_category(),
        top_events=analytics_repo.top_events(),
        no_registration=analytics_repo.users_without_registration(),
        above_average=above_average,
        average_occupancy=average,
        tags=analytics_repo.tag_usage(),
        months=analytics_repo.by_month(),
    )

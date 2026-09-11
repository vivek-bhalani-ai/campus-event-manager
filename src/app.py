"""Flask application factory for Campus Event Manager."""
from flask import Flask, render_template

from src.errors import AppError
from src.routes.analytics import analytics_bp
from src.routes.dashboard import dashboard_bp
from src.routes.events import events_bp
from src.routes.users import users_bp


def format_datetime(value, fmt="%d %b %Y, %H:%M"):
    if not value:
        return "-"
    return value.strftime(fmt)


def create_app():
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    app.secret_key = "campus-event-manager-dev"

    app.jinja_env.filters["dt"] = format_datetime

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(analytics_bp)

    @app.errorhandler(AppError)
    def handle_app_error(error):
        return render_template("error.html", message=error.message), error.status

    @app.errorhandler(404)
    def handle_404(_error):
        return render_template("error.html", message="Page not found."), 404

    return app

from flask import Blueprint, flash, redirect, render_template, request, url_for

from src.errors import AppError, clean_event_form, parse_object_id
from src.repositories import events_repo, users_repo

events_bp = Blueprint("events", __name__, url_prefix="/events")


@events_bp.route("/")
def index():
    rows = events_repo.list_events(
        search=request.args.get("search", "").strip() or None,
        category=request.args.get("category") or None,
        tag=request.args.get("tag") or None,
        when=request.args.get("when") or None,
        sort=request.args.get("sort", "asc"),
    )
    return render_template(
        "events.html",
        events=rows,
        categories=events_repo.distinct_categories(),
        tags=events_repo.distinct_tags(),
        filters=request.args,
    )


@events_bp.route("/new", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        try:
            event_id = events_repo.create_event(clean_event_form(request.form))
        except AppError as error:
            flash(error.message, "error")
            return render_template(
                "event_form.html", event=request.form,
                organizers=users_repo.list_choices(), mode="create",
            )
        flash("Event created.", "success")
        return redirect(url_for("events.detail", event_id=event_id))

    return render_template(
        "event_form.html", event=None,
        organizers=users_repo.list_choices(), mode="create",
    )


@events_bp.route("/<event_id>/edit", methods=["GET", "POST"])
def edit(event_id):
    oid = parse_object_id(event_id, "event id")
    if request.method == "POST":
        try:
            events_repo.update_event(oid, clean_event_form(request.form))
        except AppError as error:
            flash(error.message, "error")
            return redirect(url_for("events.edit", event_id=event_id))
        flash("Event updated.", "success")
        return redirect(url_for("events.detail", event_id=event_id))

    return render_template(
        "event_form.html", event=events_repo.get_event(oid),
        organizers=users_repo.list_choices(), mode="edit",
    )


@events_bp.route("/<event_id>/delete", methods=["POST"])
def delete(event_id):
    events_repo.delete_event(parse_object_id(event_id, "event id"))
    flash("Event deleted.", "success")
    return redirect(url_for("events.index"))


@events_bp.route("/<event_id>")
def detail(event_id):
    oid = parse_object_id(event_id, "event id")
    return render_template(
        "event_detail.html",
        event=events_repo.get_event(oid),
        candidates=users_repo.list_choices(),
    )


@events_bp.route("/<event_id>/registrations", methods=["POST"])
def register(event_id):
    oid = parse_object_id(event_id, "event id")
    uid = parse_object_id(request.form.get("userId"), "user id")
    status = request.form.get("status", "confirmed")
    try:
        events_repo.register_user(oid, uid, status)
        flash("Registration saved.", "success")
    except AppError as error:
        flash(error.message, "error")
    return redirect(url_for("events.detail", event_id=event_id))


@events_bp.route("/<event_id>/registrations/<user_id>/cancel", methods=["POST"])
def cancel(event_id, user_id):
    oid = parse_object_id(event_id, "event id")
    uid = parse_object_id(user_id, "user id")
    try:
        events_repo.cancel_registration(oid, uid)
        flash("Registration cancelled.", "success")
    except AppError as error:
        flash(error.message, "error")
    return redirect(url_for("events.detail", event_id=event_id))


@events_bp.route("/<event_id>/registrations/<user_id>/remove", methods=["POST"])
def remove(event_id, user_id):
    oid = parse_object_id(event_id, "event id")
    uid = parse_object_id(user_id, "user id")
    try:
        events_repo.remove_registration(oid, uid)
        flash("Registration removed.", "success")
    except AppError as error:
        flash(error.message, "error")
    return redirect(url_for("events.detail", event_id=event_id))

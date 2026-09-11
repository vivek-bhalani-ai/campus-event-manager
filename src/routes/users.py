from flask import Blueprint, flash, redirect, render_template, request, url_for

from src.errors import AppError, clean_user_form, parse_object_id
from src.repositories import users_repo

users_bp = Blueprint("users", __name__, url_prefix="/users")


@users_bp.route("/")
def index():
    rows = users_repo.list_users(
        search=request.args.get("search", "").strip() or None,
        department=request.args.get("department") or None,
        role=request.args.get("role") or None,
    )
    return render_template(
        "users.html",
        users=rows,
        departments=users_repo.distinct_departments(),
        filters=request.args,
    )


@users_bp.route("/new", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        try:
            user_id = users_repo.create_user(clean_user_form(request.form))
        except AppError as error:
            flash(error.message, "error")
            return render_template("user_form.html", user=request.form, mode="create")
        flash("User created.", "success")
        return redirect(url_for("users.detail", user_id=user_id))

    return render_template("user_form.html", user=None, mode="create")


@users_bp.route("/<user_id>/edit", methods=["GET", "POST"])
def edit(user_id):
    oid = parse_object_id(user_id, "user id")
    if request.method == "POST":
        try:
            users_repo.update_user(oid, clean_user_form(request.form))
        except AppError as error:
            flash(error.message, "error")
            return redirect(url_for("users.edit", user_id=user_id))
        flash("User updated.", "success")
        return redirect(url_for("users.detail", user_id=user_id))

    return render_template("user_form.html", user=users_repo.get_user(oid), mode="edit")


@users_bp.route("/<user_id>/delete", methods=["POST"])
def delete(user_id):
    oid = parse_object_id(user_id, "user id")
    cascade = request.form.get("cascade") == "1"
    try:
        users_repo.delete_user(oid, cascade=cascade)
        flash("User deleted.", "success")
        return redirect(url_for("users.index"))
    except AppError as error:
        flash(error.message, "error")
        return redirect(url_for("users.detail", user_id=user_id))


@users_bp.route("/<user_id>")
def detail(user_id):
    oid = parse_object_id(user_id, "user id")
    user = users_repo.get_user(oid)
    history, upcoming, past = users_repo.participation_history(oid)
    return render_template(
        "user_detail.html",
        user=user,
        history=history,
        upcoming_count=upcoming,
        past_count=past,
    )

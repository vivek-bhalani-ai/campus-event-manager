"""Application level validation, mirroring the MongoDB schema validators."""
import re
from datetime import datetime

from bson import ObjectId
from bson.errors import InvalidId

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
ROLES = ["student", "teacher", "staff"]
STATUSES = ["confirmed", "cancelled", "waiting"]


class AppError(Exception):
    """Raised for any expected, user-facing problem."""

    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


def parse_object_id(value, label="identifier"):
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        raise AppError("Malformed %s: %r" % (label, value), 400)


def parse_datetime(value, label):
    if not value:
        raise AppError("%s is required." % label)
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise AppError("%s must be a valid date and time." % label)


def clean_event_form(form):
    """Validate the event create/edit form and return a MongoDB document."""
    title = (form.get("title") or "").strip()
    if not title:
        raise AppError("Event title cannot be empty.")

    category = (form.get("category") or "").strip()
    if not category:
        raise AppError("Category cannot be empty.")

    try:
        capacity = int(form.get("capacity") or 0)
    except ValueError:
        raise AppError("Capacity must be a whole number.")
    if capacity <= 0:
        raise AppError("Capacity must be greater than 0.")

    start = parse_datetime(form.get("startDate"), "Start date")
    end = parse_datetime(form.get("endDate"), "End date")
    if end < start:
        raise AppError("End date cannot be before the start date.")

    tags = [t.strip().lower() for t in (form.get("tags") or "").split(",") if t.strip()]

    building = (form.get("building") or "").strip()
    room = (form.get("room") or "").strip()
    campus = (form.get("campus") or "").strip()
    if not (building and room and campus):
        raise AppError("Location needs a building, a room and a campus.")

    return {
        "title": title,
        "description": (form.get("description") or "").strip(),
        "category": category,
        "tags": tags,
        "startDate": start,
        "endDate": end,
        "capacity": capacity,
        "location": {"building": building, "room": room, "campus": campus},
        "organizerId": parse_object_id(form.get("organizerId"), "organizer id"),
    }


def clean_user_form(form):
    """Validate the user create/edit form and return a MongoDB document."""
    first = (form.get("firstName") or "").strip()
    last = (form.get("lastName") or "").strip()
    if not first or not last:
        raise AppError("First name and last name are required.")

    email = (form.get("email") or "").strip().lower()
    if not EMAIL_RE.match(email):
        raise AppError("%r is not a valid email address." % email)

    department = (form.get("department") or "").strip()
    if not department:
        raise AppError("Department is required.")

    role = (form.get("role") or "").strip()
    if role not in ROLES:
        raise AppError("Role must be one of: %s." % ", ".join(ROLES))

    interests = [i.strip().lower() for i in (form.get("interests") or "").split(",") if i.strip()]

    return {
        "firstName": first,
        "lastName": last,
        "email": email,
        "department": department,
        "role": role,
        "interests": interests,
    }

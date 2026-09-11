"""Every MongoDB read/write touching the `users` collection lives here."""
from datetime import datetime, timezone

from pymongo.errors import DuplicateKeyError

from src.db import users
from src.errors import AppError
from src.repositories import events_repo


def now():
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------- #
# Read
# --------------------------------------------------------------------------- #
def list_users(search=None, department=None, role=None):
    """Directory list with the registration count computed by $lookup."""
    match = {}
    if search:
        match["$or"] = [                                   # logical operator
            {"firstName": {"$regex": search, "$options": "i"}},
            {"lastName": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
        ]
    if department:
        match["department"] = department
    if role:
        match["role"] = role

    pipeline = [
        {"$match": match},
        {"$lookup": {
            "from": "events",
            "let": {"uid": "$_id"},
            "pipeline": [
                {"$match": {"$expr": {"$in": ["$$uid", {"$ifNull": ["$registrations.userId", []]}]}}},
                {"$project": {"_id": 1}},
            ],
            "as": "registeredEvents",
        }},
        {"$addFields": {"registrationCount": {"$size": "$registeredEvents"}}},
        {"$project": {"registeredEvents": 0}},
        {"$sort": {"lastName": 1, "firstName": 1}},
    ]
    return list(users().aggregate(pipeline))


def get_user(user_id):
    user = users().find_one({"_id": user_id})
    if not user:
        raise AppError("User not found.", 404)
    return user


def participation_history(user_id):
    """All events the user is registered for, with status and past/upcoming split."""
    pipeline = [
        {"$match": {"registrations.userId": user_id}},
        {"$addFields": {
            "myRegistration": {
                "$first": {
                    "$filter": {
                        "input": "$registrations",
                        "as": "r",
                        "cond": {"$eq": ["$$r.userId", user_id]},
                    }
                }
            }
        }},
        {"$project": {
            "title": 1, "category": 1, "startDate": 1, "endDate": 1,
            "location": 1, "capacity": 1,
            "status": "$myRegistration.status",
            "registeredAt": "$myRegistration.registeredAt",
        }},
        {"$sort": {"startDate": -1}},
    ]
    from src.db import events as events_collection
    rows = list(events_collection().aggregate(pipeline))

    reference = now()
    upcoming = sum(1 for r in rows if r["startDate"].replace(tzinfo=timezone.utc) >= reference)
    return rows, upcoming, len(rows) - upcoming


def list_choices():
    """Light projection used by dropdowns."""
    return list(
        users()
        .find({}, {"firstName": 1, "lastName": 1, "email": 1})   # projection
        .sort([("lastName", 1), ("firstName", 1)])
    )


def distinct_departments():
    return sorted(users().distinct("department"))


# --------------------------------------------------------------------------- #
# Write
# --------------------------------------------------------------------------- #
def create_user(doc):
    doc["createdAt"] = now()
    try:
        return users().insert_one(doc).inserted_id
    except DuplicateKeyError:
        raise AppError("A user with the email %s already exists." % doc["email"], 409)


def update_user(user_id, doc):
    try:
        result = users().update_one({"_id": user_id}, {"$set": doc})
    except DuplicateKeyError:
        raise AppError("A user with the email %s already exists." % doc["email"], 409)
    if result.matched_count == 0:
        raise AppError("User not found.", 404)


def delete_user(user_id, cascade=False):
    """Deletion strategy: block while the user is still referenced, unless the
    caller explicitly asks to remove the registrations first."""
    if events_repo.count_events_organized_by(user_id):
        raise AppError(
            "This user organises at least one event. Reassign those events first.", 409
        )

    referenced = events_repo.count_registrations_of_user(user_id)
    if referenced and not cascade:
        raise AppError(
            "This user is registered for %d event(s). Use 'Delete with registrations' "
            "to remove them first." % referenced,
            409,
        )
    if referenced:
        events_repo.remove_all_registrations_of_user(user_id)

    result = users().delete_one({"_id": user_id})
    if result.deleted_count == 0:
        raise AppError("User not found.", 404)

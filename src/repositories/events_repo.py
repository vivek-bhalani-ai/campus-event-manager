"""Every MongoDB read/write touching the `events` collection lives here."""
from datetime import datetime, timezone

from src.db import events
from src.errors import AppError

# Reusable expression: number of registrations whose status is "confirmed".
CONFIRMED_COUNT = {
    "$size": {
        "$filter": {
            "input": {"$ifNull": ["$registrations", []]},
            "as": "r",
            "cond": {"$eq": ["$$r.status", "confirmed"]},
        }
    }
}


def now():
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------- #
# Read
# --------------------------------------------------------------------------- #
def list_events(search=None, category=None, tag=None, when=None, sort="asc"):
    """Catalog query: text search, category filter, tag filter, past/upcoming."""
    match = {}
    if search:
        match["title"] = {"$regex": search, "$options": "i"}
    if category:
        match["category"] = category
    if tag:
        match["tags"] = tag                       # query on an array field
    if when == "upcoming":
        match["startDate"] = {"$gte": now()}      # comparison operator
    elif when == "past":
        match["startDate"] = {"$lt": now()}

    pipeline = [
        {"$match": match},
        {"$addFields": {"confirmedCount": CONFIRMED_COUNT}},
        {"$addFields": {"isFull": {"$gte": ["$confirmedCount", "$capacity"]}}},
        {"$project": {                            # projection
            "title": 1, "category": 1, "tags": 1, "startDate": 1, "endDate": 1,
            "capacity": 1, "location": 1, "organizerId": 1,
            "confirmedCount": 1, "isFull": 1,
        }},
        {"$sort": {"startDate": 1 if sort == "asc" else -1}},
    ]
    return list(events().aggregate(pipeline))


def get_event(event_id):
    """Detail view: event + organizer + participant details, via $lookup."""
    pipeline = [
        {"$match": {"_id": event_id}},
        {"$addFields": {"confirmedCount": CONFIRMED_COUNT}},
        {"$addFields": {
            "occupancy": {
                "$round": [
                    {"$multiply": [
                        {"$divide": ["$confirmedCount", {"$max": ["$capacity", 1]}]}, 100]},
                    1,
                ]
            }
        }},
        {"$lookup": {
            "from": "users",
            "localField": "organizerId",
            "foreignField": "_id",
            "as": "organizer",
        }},
        {"$unwind": {"path": "$organizer", "preserveNullAndEmptyArrays": True}},
        {"$lookup": {
            "from": "users",
            "localField": "registrations.userId",
            "foreignField": "_id",
            "as": "participants",
        }},
    ]
    result = list(events().aggregate(pipeline))
    if not result:
        raise AppError("Event not found.", 404)

    event = result[0]
    by_id = {u["_id"]: u for u in event.get("participants", [])}
    rows = []
    for reg in event.get("registrations", []):
        user = by_id.get(reg["userId"])
        rows.append({
            "user": user,
            "userId": reg["userId"],
            "status": reg["status"],
            "registeredAt": reg["registeredAt"],
        })
    rows.sort(key=lambda r: (r["status"] != "confirmed", r["registeredAt"]))
    event["participantRows"] = rows
    return event


def distinct_categories():
    return sorted(events().distinct("category"))


def distinct_tags():
    return sorted(events().distinct("tags"))


# --------------------------------------------------------------------------- #
# Write
# --------------------------------------------------------------------------- #
def create_event(doc):
    doc["registrations"] = []
    doc["createdAt"] = now()
    return events().insert_one(doc).inserted_id


def update_event(event_id, doc):
    """Updates scalar fields, the embedded location object and the tags array."""
    result = events().update_one({"_id": event_id}, {"$set": doc})
    if result.matched_count == 0:
        raise AppError("Event not found.", 404)


def delete_event(event_id):
    result = events().delete_one({"_id": event_id})
    if result.deleted_count == 0:
        raise AppError("Event not found.", 404)


# --------------------------------------------------------------------------- #
# Registrations - array update operators
# --------------------------------------------------------------------------- #
def register_user(event_id, user_id, status="confirmed"):
    event = events().find_one(
        {"_id": event_id}, {"capacity": 1, "registrations": 1}
    )
    if not event:
        raise AppError("Event not found.", 404)

    for reg in event.get("registrations", []):
        if reg["userId"] == user_id and reg["status"] != "cancelled":
            raise AppError("This user is already registered for the event.", 409)

    confirmed = sum(1 for r in event.get("registrations", []) if r["status"] == "confirmed")
    if status == "confirmed" and confirmed >= event["capacity"]:
        raise AppError("The event is full. Add the user to the waiting list instead.", 409)

    entry = {"userId": user_id, "registeredAt": now(), "status": status}

    # Re-activating a previously cancelled entry uses the positional operator.
    updated = events().update_one(
        {"_id": event_id, "registrations.userId": user_id},
        {"$set": {"registrations.$.status": status,
                  "registrations.$.registeredAt": entry["registeredAt"]}},
    )
    if updated.matched_count:
        return

    # New entry: $push guarded by a filter that rejects duplicates.
    pushed = events().update_one(
        {"_id": event_id, "registrations.userId": {"$ne": user_id}},
        {"$push": {"registrations": entry}},
    )
    if pushed.modified_count == 0:
        raise AppError("This user is already registered for the event.", 409)


def cancel_registration(event_id, user_id):
    """Keeps the history: sets the embedded status to `cancelled`."""
    result = events().update_one(
        {"_id": event_id, "registrations.userId": user_id},
        {"$set": {"registrations.$.status": "cancelled"}},
    )
    if result.matched_count == 0:
        raise AppError("Registration not found.", 404)


def remove_registration(event_id, user_id):
    """Deletes the embedded document from the array with $pull."""
    result = events().update_one(
        {"_id": event_id},
        {"$pull": {"registrations": {"userId": user_id}}},
    )
    if result.modified_count == 0:
        raise AppError("Registration not found.", 404)


def remove_all_registrations_of_user(user_id):
    """Referential cleanup used before deleting a user."""
    return events().update_many(
        {"registrations.userId": user_id},
        {"$pull": {"registrations": {"userId": user_id}}},
    ).modified_count


def count_events_organized_by(user_id):
    return events().count_documents({"organizerId": user_id})


def count_registrations_of_user(user_id):
    return events().count_documents({"registrations.userId": user_id})

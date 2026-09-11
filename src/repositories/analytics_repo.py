"""Aggregation pipelines behind the Dashboard and the Analytics page."""
from datetime import datetime, timezone

from src.db import events, users
from src.repositories.events_repo import CONFIRMED_COUNT

OCCUPANCY = {
    "$round": [
        {"$multiply": [
            {"$divide": ["$confirmedCount", {"$max": ["$capacity", 1]}]}, 100]},
        1,
    ]
}


def now():
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------- #
# Dashboard
# --------------------------------------------------------------------------- #
def dashboard():
    reference = now()

    total_registrations = next(
        events().aggregate([
            {"$unwind": "$registrations"},
            {"$match": {"registrations.status": {"$ne": "cancelled"}}},
            {"$count": "total"},
        ]),
        {"total": 0},
    )["total"]

    next_events = list(events().aggregate([
        {"$match": {"startDate": {"$gte": reference}}},
        {"$addFields": {"confirmedCount": CONFIRMED_COUNT}},
        {"$project": {"title": 1, "category": 1, "startDate": 1,
                      "location": 1, "capacity": 1, "confirmedCount": 1}},
        {"$sort": {"startDate": 1}},
        {"$limit": 5},
    ]))

    most_popular = next(events().aggregate([
        {"$addFields": {"confirmedCount": CONFIRMED_COUNT}},
        {"$addFields": {"occupancy": OCCUPANCY}},
        {"$sort": {"confirmedCount": -1}},
        {"$limit": 1},
    ]), None)

    return {
        "userCount": users().count_documents({}),
        "eventCount": events().count_documents({}),
        "upcomingCount": events().count_documents({"startDate": {"$gte": reference}}),
        "registrationCount": total_registrations,
        "nextEvents": next_events,
        "mostPopular": most_popular,
    }


# --------------------------------------------------------------------------- #
# Analysis A - registrations per category
# --------------------------------------------------------------------------- #
def by_category():
    return list(events().aggregate([
        {"$addFields": {"confirmedCount": CONFIRMED_COUNT}},
        {"$group": {
            "_id": "$category",
            "eventCount": {"$sum": 1},
            "registrations": {"$sum": "$confirmedCount"},
        }},
        {"$sort": {"registrations": -1, "_id": 1}},
    ]))


# --------------------------------------------------------------------------- #
# Analysis B - top 5 most popular events
# --------------------------------------------------------------------------- #
def top_events(limit=5):
    return list(events().aggregate([
        {"$addFields": {"confirmedCount": CONFIRMED_COUNT}},
        {"$addFields": {"occupancy": OCCUPANCY}},
        {"$project": {"title": 1, "category": 1, "capacity": 1,
                      "confirmedCount": 1, "occupancy": 1}},
        {"$sort": {"confirmedCount": -1, "occupancy": -1}},
        {"$limit": limit},
    ]))


# --------------------------------------------------------------------------- #
# Analysis C - users without any registration
# --------------------------------------------------------------------------- #
def users_without_registration():
    return list(users().aggregate([
        {"$lookup": {
            "from": "events",
            "let": {"uid": "$_id"},
            "pipeline": [
                {"$match": {"$expr": {"$in": ["$$uid", {"$ifNull": ["$registrations.userId", []]}]}}},
                {"$limit": 1},
                {"$project": {"_id": 1}},
            ],
            "as": "registeredEvents",
        }},
        {"$match": {"registeredEvents": {"$size": 0}}},
        {"$project": {"firstName": 1, "lastName": 1, "email": 1,
                      "department": 1, "role": 1, "interests": 1}},
        {"$sort": {"lastName": 1}},
    ]))


# --------------------------------------------------------------------------- #
# Analysis D - events above the average occupancy rate
# --------------------------------------------------------------------------- #
def above_average_occupancy():
    pipeline = [
        {"$addFields": {"confirmedCount": CONFIRMED_COUNT}},
        {"$addFields": {"occupancy": OCCUPANCY}},
        {"$group": {
            "_id": None,
            "averageOccupancy": {"$avg": "$occupancy"},
            "events": {"$push": {
                "title": "$title", "category": "$category",
                "capacity": "$capacity", "confirmedCount": "$confirmedCount",
                "occupancy": "$occupancy",
            }},
        }},
        {"$unwind": "$events"},
        {"$match": {"$expr": {"$gt": ["$events.occupancy", "$averageOccupancy"]}}},
        {"$project": {
            "_id": 0,
            "averageOccupancy": {"$round": ["$averageOccupancy", 1]},
            "title": "$events.title",
            "category": "$events.category",
            "capacity": "$events.capacity",
            "confirmedCount": "$events.confirmedCount",
            "occupancy": "$events.occupancy",
        }},
        {"$sort": {"occupancy": -1}},
    ]
    rows = list(events().aggregate(pipeline))
    average = rows[0]["averageOccupancy"] if rows else 0
    return rows, average


# --------------------------------------------------------------------------- #
# Analysis E - most used tags
# --------------------------------------------------------------------------- #
def tag_usage():
    return list(events().aggregate([
        {"$unwind": "$tags"},
        {"$group": {"_id": "$tags", "eventCount": {"$sum": 1}}},
        {"$sort": {"eventCount": -1, "_id": 1}},
    ]))


# --------------------------------------------------------------------------- #
# Analysis F - events per month
# --------------------------------------------------------------------------- #
def by_month():
    return list(events().aggregate([
        {"$addFields": {"confirmedCount": CONFIRMED_COUNT}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m", "date": "$startDate"}},
            "eventCount": {"$sum": 1},
            "registrations": {"$sum": "$confirmedCount"},
        }},
        {"$sort": {"_id": 1}},
    ]))

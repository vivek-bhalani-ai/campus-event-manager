# Campus Event Manager

A small web application that manages campus events, users and registrations on top of a
MongoDB document database. Built for the MCS DE1 NoSQL Development Project.

Author: Vivek Bhalani

## 1. What the application does

- lists, creates, edits and deletes campus events (workshops, talks, hackathons, ...)
- registers users for an event, prevents duplicates and refuses confirmed registrations
  once the event is full
- keeps a participation history per user
- computes campus activity indicators with MongoDB aggregation pipelines

## 2. Technology

| Layer     | Choice                                    |
|-----------|-------------------------------------------|
| Database  | MongoDB 8 (MongoDB Atlas free cluster)    |
| Driver    | PyMongo                                   |
| Backend   | Python 3.13 + Flask (blueprints)          |
| Frontend  | Jinja2 server-side templates + plain CSS  |

No ODM is used: every query and pipeline is written with the MongoDB driver and lives in
`src/repositories/`, so the operations are directly readable.

## 3. Install

```bash
git clone <this-repository>
cd campus-event-manager

python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

pip install -r requirements.txt
```

## 4. Configure the MongoDB connection

Copy the example file and fill in your own connection string:

```bash
copy .env.example .env        # Windows
# cp .env.example .env        # macOS / Linux
```

```
MONGODB_URI="mongodb+srv://<user>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority"
DB_NAME=campus_events
```

A local server works too: `MONGODB_URI="mongodb://localhost:27017"`.
`.env` is listed in `.gitignore`; no credential is committed.

## 5. Initialise and seed the database

Requires `mongosh` (`winget install MongoDB.Shell`, or download from mongodb.com).

```bash
mongosh "<MONGODB_URI>" database/init.js    # collections, validators, indexes
mongosh "<MONGODB_URI>" database/seed.js    # 15 users, 18 events, 63 registrations
```

`init.js` creates the JSON-Schema validators and six indexes, including the unique index on
`users.email`, plus indexes on `events.startDate`, `events.category`, `events.tags` and
`events.registrations.userId`.

`seed.js` is idempotent: it clears both collections before inserting, so it can be re-run at
any time. It produces 6 categories, 12 tags, past and upcoming events, full events and
events with no registration at all.

## 6. Run

```bash
python run.py
```

Open http://127.0.0.1:5000

## 7. Pages

| Page | Route | Content |
|------|-------|---------|
| Dashboard | `/` | user / event / upcoming / registration counters, next 5 events, most popular event |
| Events | `/events/` | catalog with search, category / tag / period filters, date sort, full indicator, create, edit, delete |
| Event detail | `/events/<id>` | full event, embedded location, organiser, occupancy, participant list, register / cancel / remove |
| Users | `/users/` | directory with search and department / role filters, CRUD, registration count |
| User detail | `/users/<id>` | profile, interests, full event history, upcoming vs past counters |
| Analytics | `/analytics/` | six aggregation analyses (A to F) |

## 8. Where the MongoDB operations live

| File | Contents |
|------|----------|
| `database/init.js` | `createCollection`, `collMod`, JSON Schema validators, `createIndex` |
| `database/seed.js` | `deleteMany`, `insertMany`, `distinct`, summary aggregation |
| `src/repositories/events_repo.py` | event CRUD, array queries, `$push`, `$pull`, positional operator, `$lookup` |
| `src/repositories/users_repo.py` | user CRUD, `$or` search, `$lookup` with a sub-pipeline, projections |
| `src/repositories/analytics_repo.py` | dashboard statistics and the six analytics pipelines |

## 9. Project structure

```
campus-event-manager/
|-- README.md
|-- .gitignore
|-- .env.example
|-- requirements.txt
|-- run.py
|-- database/
|   |-- init.js
|   `-- seed.js
|-- report/
|   `-- report.pdf
`-- src/
    |-- app.py            application factory, error handlers
    |-- db.py             MongoDB client
    |-- errors.py         application-level validation
    |-- repositories/     all MongoDB operations
    |-- routes/           Flask blueprints
    |-- templates/        Jinja2 pages
    `-- static/           stylesheet
```

## 10. Error handling

The application returns a readable message for: duplicate email, invalid capacity,
end date before start date, missing user or event, duplicate registration, full event,
malformed ObjectId, and deletion of a user still referenced by events. A user who organises
an event cannot be deleted; a user with registrations only can be deleted together with
those registrations.

// ---------------------------------------------------------------------------
// Campus Event Manager - reproducible seed data
// Wipes and repopulates `users` and `events`.
//
// Run with:  mongosh "<MONGODB_URI>" database/seed.js
// (run database/init.js first so validators and indexes exist)
// ---------------------------------------------------------------------------

const database = db.getSiblingDB("campus_events");

database.events.deleteMany({});
database.users.deleteMany({});

const now = new Date();
function day(offset, hour) {
  const d = new Date(now.getTime() + offset * 86400000);
  d.setUTCHours(hour, 0, 0, 0);
  return d;
}

// --- 15 users --------------------------------------------------------------
const userSeed = [
  ["Amelie",  "Rousseau", "amelie.rousseau@campus.edu",  "Data Engineering", "student", ["machine learning", "python", "hackathons"]],
  ["Karim",   "Benali",   "karim.benali@campus.edu",     "Data Engineering", "student", ["cloud", "devops", "python"]],
  ["Sofia",   "Marchetti","sofia.marchetti@campus.edu",  "Business",         "student", ["entrepreneurship", "marketing"]],
  ["Lucas",   "Fernandez","lucas.fernandez@campus.edu",  "Computer Science", "student", ["cybersecurity", "networks"]],
  ["Priya",   "Nair",     "priya.nair@campus.edu",       "Data Engineering", "student", ["nosql", "databases", "python"]],
  ["Tom",     "Weber",    "tom.weber@campus.edu",        "Design",           "student", ["ux", "prototyping"]],
  ["Ines",    "Diallo",   "ines.diallo@campus.edu",      "Business",         "student", ["finance", "public speaking"]],
  ["Jonas",   "Lindqvist","jonas.lindqvist@campus.edu",  "Computer Science", "student", ["open source", "linux"]],
  ["Mei",     "Chen",     "mei.chen@campus.edu",         "Data Engineering", "student", ["statistics", "visualisation"]],
  ["Rafael",  "Costa",    "rafael.costa@campus.edu",     "Design",           "student", ["illustration", "ux"]],
  ["Claire",  "Dubois",   "claire.dubois@campus.edu",    "Data Engineering", "teacher", ["nosql", "distributed systems"]],
  ["Hugo",    "Petit",    "hugo.petit@campus.edu",       "Computer Science", "teacher", ["algorithms", "cybersecurity"]],
  ["Nadia",   "Haddad",   "nadia.haddad@campus.edu",     "Business",         "teacher", ["strategy", "entrepreneurship"]],
  ["Erik",    "Johansson","erik.johansson@campus.edu",   "Student Services", "staff",   ["community", "wellbeing"]],
  ["Laura",   "Moreau",   "laura.moreau@campus.edu",     "Student Services", "staff",   ["events", "logistics"]]
];

const users = userSeed.map(function (u, i) {
  return {
    _id: new ObjectId(),
    firstName: u[0],
    lastName: u[1],
    email: u[2],
    department: u[3],
    role: u[4],
    interests: u[5],
    createdAt: day(-120 + i, 9)
  };
});
database.users.insertMany(users);

const id = {};
users.forEach(function (u) { id[u.email.split("@")[0]] = u._id; });
const U = users.map(function (u) { return u._id; });

// --- 18 events -------------------------------------------------------------
// 6 categories, 12 tags, dates spread from May to December 2026.
// dayOffset < 0 = past event, > 0 = upcoming event.
const eventSeed = [
  // [title, category, tags, dayOffset, durationHours, capacity, building, room, campus, organizerIndex, nbConfirmed, nbWaiting, nbCancelled]
  ["Intro to MongoDB Aggregation", "Workshop",  ["nosql", "databases", "python"],        -112, 3, 30, "Innovation Center", "B204", "Paris",   10, 5, 0, 1],
  ["Cloud Cost Optimisation Talk", "Talk",      ["cloud", "devops"],                      -95, 2, 60, "Main Building",     "A101", "Paris",   11, 4, 0, 0],
  ["Spring Design Sprint",         "Workshop",  ["ux", "prototyping", "design"],          -74, 6, 20, "Design Lab",        "D12",  "Paris",    9, 6, 0, 0],
  ["Data Ethics Roundtable",       "Talk",      ["ethics", "data"],                       -60, 2, 40, "Main Building",     "A203", "Paris",   12, 3, 0, 1],
  ["Summer Hack Night",            "Hackathon", ["hackathons", "python", "open source"],  -45, 8, 50, "Innovation Center", "B100", "Paris",   10, 8, 0, 0],
  ["Alumni Networking Evening",    "Networking",["career", "community"],                  -30, 3, 80, "Main Building",     "Hall", "Paris",   14, 5, 0, 0],
  ["Wellbeing Yoga Session",       "Social",    ["wellbeing", "community"],               -21, 1, 25, "Sports Center",     "S01",  "Paris",   13, 0, 0, 0],
  ["Linux Fundamentals Lab",       "Workshop",  ["linux", "open source"],                 -12, 4, 24, "Computer Lab",      "C05",  "Saclay",  11, 4, 1, 0],
  ["Kickoff: Autumn Semester",     "Talk",      ["community"],                             -3, 2, 100,"Main Building",     "Hall", "Paris",   14, 6, 0, 0],

  ["NoSQL Modeling Deep Dive",     "Workshop",  ["nosql", "databases"],                     4, 3, 25, "Innovation Center", "B204", "Paris",   10, 5, 2, 0],
  ["Cybersecurity Capture the Flag","Hackathon",["cybersecurity", "networks"],              9, 6, 40, "Computer Lab",      "C11",  "Saclay",  11, 7, 0, 1],
  ["Startup Pitch Practice",       "Networking",["entrepreneurship", "career"],            15, 2, 30, "Business School",   "E20",  "Paris",   12, 3, 0, 0],
  ["Data Visualisation Clinic",    "Workshop",  ["visualisation", "data"],                 23, 3, 20, "Innovation Center", "B210", "Paris",    8, 4, 0, 0],
  ["Careers in Cloud Panel",       "Talk",      ["cloud", "career"],                       34, 2, 70, "Main Building",     "A101", "Paris",   13, 2, 0, 0],
  ["Board Games Evening",          "Social",    ["community", "wellbeing"],                41, 4, 35, "Student House",     "SH1",  "Paris",   14, 0, 0, 0],
  ["Autumn Hackathon 48h",         "Hackathon", ["hackathons", "cloud", "open source"],    56, 48, 60,"Innovation Center", "B100", "Paris",   10, 9, 3, 0],
  ["Research Poster Session",      "Conference",["research", "data"],                      74, 5, 45, "Main Building",     "Atrium","Paris",  12, 0, 0, 0],
  ["Winter Tech Conference",       "Conference",["cloud", "nosql", "research"],            96, 8, 120,"Convention Wing",   "W1",   "Saclay",  11, 6, 0, 2]
];

// Deterministic participant picking so the seed is reproducible.
let cursor = 0;
function takeUsers(n, organizerId) {
  const picked = [];
  while (picked.length < n) {
    const candidate = U[cursor % U.length];
    cursor += 1;
    if (String(candidate) === String(organizerId)) { continue; }
    if (picked.some(function (p) { return String(p) === String(candidate); })) { continue; }
    picked.push(candidate);
  }
  return picked;
}

const events = eventSeed.map(function (e, index) {
  const organizerId = U[e[9]];
  const start = day(e[3], 10);
  const end = new Date(start.getTime() + e[4] * 3600000);

  const total = e[10] + e[11] + e[12];
  const participants = takeUsers(total, organizerId);

  const registrations = participants.map(function (userId, i) {
    let status = "confirmed";
    if (i >= e[10] && i < e[10] + e[11]) { status = "waiting"; }
    if (i >= e[10] + e[11]) { status = "cancelled"; }
    return {
      userId: userId,
      registeredAt: new Date(start.getTime() - (i + 2) * 86400000),
      status: status
    };
  });

  return {
    _id: new ObjectId(),
    title: e[0],
    description: e[0] + " - organised by the campus community. Open to all students and staff.",
    category: e[1],
    tags: e[2],
    startDate: start,
    endDate: end,
    capacity: NumberInt(e[5]),
    location: { building: e[6], room: e[7], campus: e[8] },
    organizerId: organizerId,
    registrations: registrations,
    createdAt: new Date(start.getTime() - 30 * 86400000)
  };
});

database.events.insertMany(events);

// --- summary ---------------------------------------------------------------
const totalRegs = database.events.aggregate([
  { $project: { n: { $size: "$registrations" } } },
  { $group: { _id: null, total: { $sum: "$n" } } }
]).toArray()[0].total;

print("users           : " + database.users.countDocuments());
print("events          : " + database.events.countDocuments());
print("categories      : " + database.events.distinct("category").length);
print("tags            : " + database.events.distinct("tags").length);
print("registrations   : " + totalRegs);
print("events with none: " + database.events.countDocuments({ registrations: { $size: 0 } }));
print("\nseed.js completed.");

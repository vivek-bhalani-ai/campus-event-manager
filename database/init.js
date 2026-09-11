// ---------------------------------------------------------------------------
// Campus Event Manager - database initialisation
// Creates the `campus_events` collections, their JSON-Schema validators and
// the indexes required by the application queries.
//
// Run with:  mongosh "<MONGODB_URI>" database/init.js
// ---------------------------------------------------------------------------

const database = db.getSiblingDB("campus_events");

// --- users -----------------------------------------------------------------
// Rules: email must look like an email and is unique (see index below),
// role and department are mandatory, interests is always an array.
const userValidator = {
  $jsonSchema: {
    bsonType: "object",
    required: ["firstName", "lastName", "email", "department", "role", "interests", "createdAt"],
    properties: {
      firstName: { bsonType: "string", minLength: 1 },
      lastName: { bsonType: "string", minLength: 1 },
      email: { bsonType: "string", pattern: "^[^@\\s]+@[^@\\s]+\\.[A-Za-z]{2,}$" },
      department: { bsonType: "string", minLength: 1 },
      role: { enum: ["student", "teacher", "staff"] },
      interests: { bsonType: "array", items: { bsonType: "string" } },
      createdAt: { bsonType: "date" }
    }
  }
};

// --- events ----------------------------------------------------------------
// Rules: title cannot be empty, capacity > 0, endDate >= startDate,
// location is an embedded object, tags an array of strings and registrations
// an array of embedded documents with a controlled status.
const eventValidator = {
  $and: [
    {
      $jsonSchema: {
        bsonType: "object",
        required: ["title", "category", "tags", "startDate", "endDate", "capacity",
                   "location", "organizerId", "registrations", "createdAt"],
        properties: {
          title: { bsonType: "string", minLength: 1 },
          description: { bsonType: "string" },
          category: { bsonType: "string", minLength: 1 },
          tags: { bsonType: "array", items: { bsonType: "string" } },
          startDate: { bsonType: "date" },
          endDate: { bsonType: "date" },
          capacity: { bsonType: "int", minimum: 1 },
          location: {
            bsonType: "object",
            required: ["building", "room", "campus"],
            properties: {
              building: { bsonType: "string" },
              room: { bsonType: "string" },
              campus: { bsonType: "string" }
            }
          },
          organizerId: { bsonType: "objectId" },
          registrations: {
            bsonType: "array",
            items: {
              bsonType: "object",
              required: ["userId", "registeredAt", "status"],
              properties: {
                userId: { bsonType: "objectId" },
                registeredAt: { bsonType: "date" },
                status: { enum: ["confirmed", "cancelled", "waiting"] }
              }
            }
          },
          createdAt: { bsonType: "date" }
        }
      }
    },
    // Cross-field rule that JSON Schema cannot express on its own.
    { $expr: { $gte: ["$endDate", "$startDate"] } }
  ]
};

function ensureCollection(name, validator) {
  const exists = database.getCollectionNames().indexOf(name) !== -1;
  if (exists) {
    database.runCommand({ collMod: name, validator: validator, validationLevel: "moderate" });
    print("collMod  -> " + name);
  } else {
    database.createCollection(name, { validator: validator, validationLevel: "moderate" });
    print("created  -> " + name);
  }
}

ensureCollection("users", userValidator);
ensureCollection("events", eventValidator);

// --- indexes ---------------------------------------------------------------
database.users.createIndex({ email: 1 }, { unique: true, name: "uniq_email" });
database.users.createIndex({ department: 1, role: 1 }, { name: "idx_department_role" });

database.events.createIndex({ startDate: 1 }, { name: "idx_startDate" });
database.events.createIndex({ category: 1 }, { name: "idx_category" });
database.events.createIndex({ tags: 1 }, { name: "idx_tags" });
database.events.createIndex({ "registrations.userId": 1 }, { name: "idx_registration_user" });

print("\nusers indexes : " + database.users.getIndexes().map(i => i.name).join(", "));
print("events indexes: " + database.events.getIndexes().map(i => i.name).join(", "));
print("\ninit.js completed.");

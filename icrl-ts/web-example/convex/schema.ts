import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  // Databases (ICRL instances)
  databases: defineTable({
    name: v.string(),
    description: v.optional(v.string()),
    systemPrompt: v.optional(v.string()),
    createdAt: v.number(),
    updatedAt: v.number(),
  }).index("by_name", ["name"]),

  // Examples (training data for RLHF)
  examples: defineTable({
    databaseId: v.id("databases"),
    question: v.string(),
    chosenAnswer: v.string(),
    rejectedAnswer: v.optional(v.string()),
    isCustom: v.boolean(),
    createdAt: v.number(),
    timesRetrieved: v.number(),
    // Embedding for vector search (optional, can be added later)
    embedding: v.optional(v.array(v.float64())),
  })
    .index("by_database", ["databaseId"])
    .index("by_database_created", ["databaseId", "createdAt"]),
});

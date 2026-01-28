import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  // Databases (ICRL instances / namespaces)
  databases: defineTable({
    name: v.string(),
    description: v.optional(v.string()),
    systemPrompt: v.optional(v.string()),
    createdAt: v.number(),
    updatedAt: v.number(),
  }).index("by_name", ["name"]),

  // Trajectories (matches icrl Trajectory type)
  trajectories: defineTable({
    // Database this trajectory belongs to
    databaseId: v.id("databases"),
    // Trajectory fields from icrl
    trajectoryId: v.string(), // The icrl internal ID
    goal: v.string(),
    plan: v.string(),
    steps: v.array(
      v.object({
        observation: v.string(),
        reasoning: v.string(),
        action: v.string(),
      })
    ),
    success: v.boolean(),
    metadata: v.optional(v.any()),
    createdAt: v.number(),
  })
    .index("by_database", ["databaseId"])
    .index("by_trajectory_id", ["databaseId", "trajectoryId"]),

  // Curation metadata for trajectories
  curationMetadata: defineTable({
    databaseId: v.id("databases"),
    trajectoryId: v.string(),
    createdAt: v.number(),
    timesRetrieved: v.number(),
    timesLedToSuccess: v.number(),
    retrievalScore: v.optional(v.number()),
    persistenceScore: v.optional(v.number()),
    utilityScore: v.number(),
    isDeprecated: v.boolean(),
    deprecatedAt: v.optional(v.number()),
    deprecationReason: v.optional(v.string()),
    supersededBy: v.optional(v.string()),
  })
    .index("by_database", ["databaseId"])
    .index("by_trajectory_id", ["databaseId", "trajectoryId"]),

  // Embeddings for vector similarity search
  embeddings: defineTable({
    databaseId: v.id("databases"),
    embeddingId: v.string(), // Unique ID for this embedding
    trajectoryId: v.string(), // Reference to trajectory
    type: v.union(v.literal("trajectory"), v.literal("step")),
    stepIndex: v.optional(v.number()), // For step embeddings
    embedding: v.array(v.float64()), // The actual vector
    createdAt: v.number(),
  })
    .index("by_database", ["databaseId"])
    .index("by_database_type", ["databaseId", "type"])
    .index("by_trajectory", ["databaseId", "trajectoryId"]),

  // Examples (human feedback data - kept for backward compatibility)
  examples: defineTable({
    databaseId: v.id("databases"),
    question: v.string(),
    chosenAnswer: v.string(),
    rejectedAnswer: v.optional(v.string()),
    isCustom: v.boolean(),
    createdAt: v.number(),
    timesRetrieved: v.number(),
  })
    .index("by_database", ["databaseId"])
    .index("by_database_created", ["databaseId", "createdAt"]),
});

import { v } from "convex/values";
import { mutation, query } from "./_generated/server";

// Step schema for validation
const stepValidator = v.object({
  observation: v.string(),
  reasoning: v.string(),
  action: v.string(),
});

// Get all trajectories for a database
export const listByDatabase = query({
  args: { databaseId: v.id("databases") },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("trajectories")
      .withIndex("by_database", (q) => q.eq("databaseId", args.databaseId))
      .collect();
  },
});

// Get a trajectory by its icrl ID
export const getByTrajectoryId = query({
  args: {
    databaseId: v.id("databases"),
    trajectoryId: v.string(),
  },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("trajectories")
      .withIndex("by_trajectory_id", (q) =>
        q.eq("databaseId", args.databaseId).eq("trajectoryId", args.trajectoryId)
      )
      .first();
  },
});

// Create a new trajectory
export const create = mutation({
  args: {
    databaseId: v.id("databases"),
    trajectoryId: v.string(),
    goal: v.string(),
    plan: v.string(),
    steps: v.array(stepValidator),
    success: v.boolean(),
    metadata: v.optional(v.any()),
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("trajectories", {
      databaseId: args.databaseId,
      trajectoryId: args.trajectoryId,
      goal: args.goal,
      plan: args.plan,
      steps: args.steps,
      success: args.success,
      metadata: args.metadata,
      createdAt: Date.now(),
    });
  },
});

// Delete a trajectory by its icrl ID
export const deleteByTrajectoryId = mutation({
  args: {
    databaseId: v.id("databases"),
    trajectoryId: v.string(),
  },
  handler: async (ctx, args) => {
    const trajectory = await ctx.db
      .query("trajectories")
      .withIndex("by_trajectory_id", (q) =>
        q.eq("databaseId", args.databaseId).eq("trajectoryId", args.trajectoryId)
      )
      .first();

    if (trajectory) {
      await ctx.db.delete(trajectory._id);
      return true;
    }
    return false;
  },
});

// Curation metadata operations

export const getCurationMetadata = query({
  args: {
    databaseId: v.id("databases"),
    trajectoryId: v.string(),
  },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("curationMetadata")
      .withIndex("by_trajectory_id", (q) =>
        q.eq("databaseId", args.databaseId).eq("trajectoryId", args.trajectoryId)
      )
      .first();
  },
});

export const getAllCurationMetadata = query({
  args: { databaseId: v.id("databases") },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("curationMetadata")
      .withIndex("by_database", (q) => q.eq("databaseId", args.databaseId))
      .collect();
  },
});

export const saveCurationMetadata = mutation({
  args: {
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
  },
  handler: async (ctx, args) => {
    // Check if metadata already exists
    const existing = await ctx.db
      .query("curationMetadata")
      .withIndex("by_trajectory_id", (q) =>
        q.eq("databaseId", args.databaseId).eq("trajectoryId", args.trajectoryId)
      )
      .first();

    if (existing) {
      // Update existing
      await ctx.db.patch(existing._id, {
        timesRetrieved: args.timesRetrieved,
        timesLedToSuccess: args.timesLedToSuccess,
        retrievalScore: args.retrievalScore,
        persistenceScore: args.persistenceScore,
        utilityScore: args.utilityScore,
        isDeprecated: args.isDeprecated,
        deprecatedAt: args.deprecatedAt,
        deprecationReason: args.deprecationReason,
        supersededBy: args.supersededBy,
      });
      return existing._id;
    } else {
      // Create new
      return await ctx.db.insert("curationMetadata", {
        databaseId: args.databaseId,
        trajectoryId: args.trajectoryId,
        createdAt: args.createdAt,
        timesRetrieved: args.timesRetrieved,
        timesLedToSuccess: args.timesLedToSuccess,
        retrievalScore: args.retrievalScore,
        persistenceScore: args.persistenceScore,
        utilityScore: args.utilityScore,
        isDeprecated: args.isDeprecated,
        deprecatedAt: args.deprecatedAt,
        deprecationReason: args.deprecationReason,
        supersededBy: args.supersededBy,
      });
    }
  },
});

export const deleteCurationMetadata = mutation({
  args: {
    databaseId: v.id("databases"),
    trajectoryId: v.string(),
  },
  handler: async (ctx, args) => {
    const metadata = await ctx.db
      .query("curationMetadata")
      .withIndex("by_trajectory_id", (q) =>
        q.eq("databaseId", args.databaseId).eq("trajectoryId", args.trajectoryId)
      )
      .first();

    if (metadata) {
      await ctx.db.delete(metadata._id);
      return true;
    }
    return false;
  },
});

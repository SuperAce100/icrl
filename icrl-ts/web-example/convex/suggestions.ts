import { v } from "convex/values";
import { mutation, query } from "./_generated/server";

// Cache TTL: 1 hour in milliseconds
const CACHE_TTL_MS = 60 * 60 * 1000;

// Get cached suggestions for a database
// Returns null if cache is stale or doesn't exist
export const getCached = query({
  args: {
    databaseId: v.id("databases"),
    currentExampleCount: v.number(),
  },
  handler: async (ctx, args) => {
    const cached = await ctx.db
      .query("suggestionCache")
      .withIndex("by_database", (q) => q.eq("databaseId", args.databaseId))
      .first();

    if (!cached) {
      return null;
    }

    // Check if cache is stale
    const isExpired = Date.now() - cached.createdAt > CACHE_TTL_MS;
    const exampleCountChanged = cached.exampleCount !== args.currentExampleCount;

    if (isExpired || exampleCountChanged) {
      return null;
    }

    return cached.suggestions;
  },
});

// Get the current example count for a database
export const getExampleCount = query({
  args: { databaseId: v.id("databases") },
  handler: async (ctx, args) => {
    const examples = await ctx.db
      .query("examples")
      .withIndex("by_database", (q) => q.eq("databaseId", args.databaseId))
      .collect();
    return examples.length;
  },
});

// Get all examples for a database (for suggestion generation)
export const getAllExamples = query({
  args: { databaseId: v.id("databases") },
  handler: async (ctx, args) => {
    const examples = await ctx.db
      .query("examples")
      .withIndex("by_database", (q) => q.eq("databaseId", args.databaseId))
      .collect();
    return examples.map((ex) => ({
      question: ex.question,
      chosenAnswer: ex.chosenAnswer,
    }));
  },
});

// Set cached suggestions for a database
// Upserts - replaces existing cache if present
export const setCache = mutation({
  args: {
    databaseId: v.id("databases"),
    suggestions: v.array(v.string()),
    exampleCount: v.number(),
    exampleHash: v.string(),
  },
  handler: async (ctx, args) => {
    // Check if cache already exists
    const existing = await ctx.db
      .query("suggestionCache")
      .withIndex("by_database", (q) => q.eq("databaseId", args.databaseId))
      .first();

    if (existing) {
      // Update existing cache
      await ctx.db.patch(existing._id, {
        suggestions: args.suggestions,
        exampleCount: args.exampleCount,
        exampleHash: args.exampleHash,
        createdAt: Date.now(),
      });
      return existing._id;
    } else {
      // Create new cache entry
      const id = await ctx.db.insert("suggestionCache", {
        databaseId: args.databaseId,
        suggestions: args.suggestions,
        exampleCount: args.exampleCount,
        exampleHash: args.exampleHash,
        createdAt: Date.now(),
      });
      return id;
    }
  },
});

// Invalidate cache for a database (force refresh)
export const invalidateCache = mutation({
  args: { databaseId: v.id("databases") },
  handler: async (ctx, args) => {
    const cached = await ctx.db
      .query("suggestionCache")
      .withIndex("by_database", (q) => q.eq("databaseId", args.databaseId))
      .first();

    if (cached) {
      await ctx.db.delete(cached._id);
    }
  },
});

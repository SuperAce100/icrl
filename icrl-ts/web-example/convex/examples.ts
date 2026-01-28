import { v } from "convex/values";
import { mutation, query } from "./_generated/server";

// List all examples for a database
export const listByDatabase = query({
  args: { databaseId: v.id("databases") },
  handler: async (ctx, args) => {
    const examples = await ctx.db
      .query("examples")
      .withIndex("by_database_created", (q) => q.eq("databaseId", args.databaseId))
      .order("desc")
      .collect();
    return examples;
  },
});

// Get a single example
export const get = query({
  args: { id: v.id("examples") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.id);
  },
});

// Create a new example (from human feedback)
export const create = mutation({
  args: {
    databaseId: v.id("databases"),
    question: v.string(),
    chosenAnswer: v.string(),
    rejectedAnswer: v.optional(v.string()),
    isCustom: v.boolean(),
  },
  handler: async (ctx, args) => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const doc: any = {
      databaseId: args.databaseId,
      question: args.question,
      chosenAnswer: args.chosenAnswer,
      isCustom: args.isCustom,
      createdAt: Date.now(),
      timesRetrieved: 0,
    };
    if (args.rejectedAnswer) doc.rejectedAnswer = args.rejectedAnswer;
    
    const id = await ctx.db.insert("examples", doc);
    return id;
  },
});

// Delete an example
export const remove = mutation({
  args: { id: v.id("examples") },
  handler: async (ctx, args) => {
    await ctx.db.delete(args.id);
    return args.id;
  },
});

// Increment retrieval count for examples
export const incrementRetrievalCount = mutation({
  args: { ids: v.array(v.id("examples")) },
  handler: async (ctx, args) => {
    for (const id of args.ids) {
      const example = await ctx.db.get(id);
      if (example) {
        await ctx.db.patch(id, {
          timesRetrieved: example.timesRetrieved + 1,
        });
      }
    }
  },
});

// Simple keyword-based search (fallback when no embeddings)
export const searchByKeyword = query({
  args: {
    databaseId: v.id("databases"),
    query: v.string(),
    limit: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const limit = args.limit ?? 3;
    const examples = await ctx.db
      .query("examples")
      .withIndex("by_database", (q) => q.eq("databaseId", args.databaseId))
      .collect();

    // Simple keyword matching
    const queryWords = new Set(
      args.query
        .toLowerCase()
        .split(/\s+/)
        .filter((w) => w.length > 2)
    );

    const scored = examples.map((example) => {
      const textWords = new Set(
        `${example.question} ${example.chosenAnswer}`
          .toLowerCase()
          .split(/\s+/)
          .filter((w) => w.length > 2)
      );

      let matches = 0;
      for (const word of queryWords) {
        if (textWords.has(word)) matches++;
      }

      const score = queryWords.size > 0 ? matches / queryWords.size : 0;
      return { example, score };
    });

    // Sort by score and return top k
    scored.sort((a, b) => b.score - a.score);
    return scored
      .slice(0, limit)
      .filter((s) => s.score > 0)
      .map((s) => s.example);
  },
});

// Get recent examples for a database
export const getRecent = query({
  args: {
    databaseId: v.id("databases"),
    limit: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const limit = args.limit ?? 10;
    const examples = await ctx.db
      .query("examples")
      .withIndex("by_database_created", (q) => q.eq("databaseId", args.databaseId))
      .order("desc")
      .take(limit);
    return examples;
  },
});

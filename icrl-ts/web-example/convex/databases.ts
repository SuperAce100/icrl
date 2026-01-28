import { v } from "convex/values";
import { mutation, query } from "./_generated/server";

// List all databases
export const list = query({
  args: {},
  handler: async (ctx) => {
    const databases = await ctx.db.query("databases").order("desc").collect();
    return databases;
  },
});

// Get a single database by ID
export const get = query({
  args: { id: v.id("databases") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.id);
  },
});

// Create a new database
export const create = mutation({
  args: {
    name: v.string(),
    description: v.optional(v.string()),
    systemPrompt: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const now = Date.now();
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const doc: any = {
      name: args.name,
      createdAt: now,
      updatedAt: now,
    };
    if (args.description) doc.description = args.description;
    if (args.systemPrompt) doc.systemPrompt = args.systemPrompt;
    
    const id = await ctx.db.insert("databases", doc);
    return id;
  },
});

// Update a database
export const update = mutation({
  args: {
    id: v.id("databases"),
    name: v.optional(v.string()),
    description: v.optional(v.string()),
    systemPrompt: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const { id, ...updates } = args;
    const existing = await ctx.db.get(id);
    if (!existing) {
      throw new Error("Database not found");
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const updateData: any = { updatedAt: Date.now() };
    if (updates.name !== undefined) updateData.name = updates.name;
    if (updates.description !== undefined) updateData.description = updates.description;
    if (updates.systemPrompt !== undefined) updateData.systemPrompt = updates.systemPrompt;

    await ctx.db.patch(id, updateData);
    return id;
  },
});

// Delete a database and all its examples
export const remove = mutation({
  args: { id: v.id("databases") },
  handler: async (ctx, args) => {
    // Delete all examples in this database
    const examples = await ctx.db
      .query("examples")
      .withIndex("by_database", (q) => q.eq("databaseId", args.id))
      .collect();

    for (const example of examples) {
      await ctx.db.delete(example._id);
    }

    // Delete the database
    await ctx.db.delete(args.id);
    return args.id;
  },
});

// Get database stats
export const getStats = query({
  args: { id: v.id("databases") },
  handler: async (ctx, args) => {
    const examples = await ctx.db
      .query("examples")
      .withIndex("by_database", (q) => q.eq("databaseId", args.id))
      .collect();

    const totalExamples = examples.length;
    const customAnswers = examples.filter((e) => e.isCustom).length;
    const totalRetrievals = examples.reduce((sum, e) => sum + e.timesRetrieved, 0);

    return {
      totalExamples,
      customAnswers,
      totalRetrievals,
    };
  },
});

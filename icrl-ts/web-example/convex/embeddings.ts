import { v } from "convex/values";
import { mutation, query } from "./_generated/server";

/**
 * Normalize a vector to unit length for cosine similarity.
 */
function normalize(vec: number[]): number[] {
  const norm = Math.sqrt(vec.reduce((sum, v) => sum + v * v, 0));
  if (norm === 0) return vec;
  return vec.map((v) => v / norm);
}

/**
 * Compute cosine similarity between two vectors.
 */
function cosineSimilarity(a: number[], b: number[]): number {
  const aNorm = normalize(a);
  const bNorm = normalize(b);
  return aNorm.reduce((sum, ai, i) => sum + ai * (bNorm[i] ?? 0), 0);
}

// Get an embedding by its ID
export const getById = query({
  args: {
    databaseId: v.id("databases"),
    embeddingId: v.string(),
  },
  handler: async (ctx, args) => {
    const embeddings = await ctx.db
      .query("embeddings")
      .withIndex("by_database", (q) => q.eq("databaseId", args.databaseId))
      .collect();

    return embeddings.find((e) => e.embeddingId === args.embeddingId) ?? null;
  },
});

// Get all embeddings of a specific type for a database
export const getByType = query({
  args: {
    databaseId: v.id("databases"),
    type: v.union(v.literal("trajectory"), v.literal("step")),
  },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("embeddings")
      .withIndex("by_database_type", (q) =>
        q.eq("databaseId", args.databaseId).eq("type", args.type)
      )
      .collect();
  },
});

// Save a single embedding
export const save = mutation({
  args: {
    databaseId: v.id("databases"),
    embeddingId: v.string(),
    trajectoryId: v.string(),
    type: v.union(v.literal("trajectory"), v.literal("step")),
    stepIndex: v.optional(v.number()),
    embedding: v.array(v.float64()),
  },
  handler: async (ctx, args) => {
    // Check if embedding already exists
    const existing = await ctx.db
      .query("embeddings")
      .withIndex("by_database", (q) => q.eq("databaseId", args.databaseId))
      .collect();

    const existingEmbed = existing.find((e) => e.embeddingId === args.embeddingId);

    if (existingEmbed) {
      // Update existing
      await ctx.db.patch(existingEmbed._id, {
        embedding: args.embedding,
      });
      return existingEmbed._id;
    } else {
      // Create new
      return await ctx.db.insert("embeddings", {
        databaseId: args.databaseId,
        embeddingId: args.embeddingId,
        trajectoryId: args.trajectoryId,
        type: args.type,
        stepIndex: args.stepIndex,
        embedding: args.embedding,
        createdAt: Date.now(),
      });
    }
  },
});

// Save multiple embeddings (batch)
export const saveBatch = mutation({
  args: {
    databaseId: v.id("databases"),
    embeddings: v.array(
      v.object({
        embeddingId: v.string(),
        trajectoryId: v.string(),
        type: v.union(v.literal("trajectory"), v.literal("step")),
        stepIndex: v.optional(v.number()),
        embedding: v.array(v.float64()),
      })
    ),
  },
  handler: async (ctx, args) => {
    const ids = [];
    for (const emb of args.embeddings) {
      const id = await ctx.db.insert("embeddings", {
        databaseId: args.databaseId,
        embeddingId: emb.embeddingId,
        trajectoryId: emb.trajectoryId,
        type: emb.type,
        stepIndex: emb.stepIndex,
        embedding: emb.embedding,
        createdAt: Date.now(),
      });
      ids.push(id);
    }
    return ids;
  },
});

// Delete all embeddings for a trajectory
export const deleteForTrajectory = mutation({
  args: {
    databaseId: v.id("databases"),
    trajectoryId: v.string(),
  },
  handler: async (ctx, args) => {
    const embeddings = await ctx.db
      .query("embeddings")
      .withIndex("by_trajectory", (q) =>
        q.eq("databaseId", args.databaseId).eq("trajectoryId", args.trajectoryId)
      )
      .collect();

    for (const emb of embeddings) {
      await ctx.db.delete(emb._id);
    }

    return embeddings.length;
  },
});

// Vector similarity search
export const search = query({
  args: {
    databaseId: v.id("databases"),
    query: v.array(v.float64()),
    type: v.union(v.literal("trajectory"), v.literal("step")),
    k: v.number(),
  },
  handler: async (ctx, args) => {
    // Get all embeddings of the specified type
    const embeddings = await ctx.db
      .query("embeddings")
      .withIndex("by_database_type", (q) =>
        q.eq("databaseId", args.databaseId).eq("type", args.type)
      )
      .collect();

    if (embeddings.length === 0) {
      return [];
    }

    // Compute similarity scores
    const scored = embeddings.map((emb) => ({
      id: emb.embeddingId,
      trajectoryId: emb.trajectoryId,
      stepIndex: emb.stepIndex,
      score: cosineSimilarity(args.query, emb.embedding),
    }));

    // Sort by score descending
    scored.sort((a, b) => b.score - a.score);

    // Return top k
    return scored.slice(0, args.k);
  },
});

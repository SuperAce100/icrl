/**
 * Convert a database name to a URL-safe slug
 */
export function toSlug(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}

/**
 * Tab values that map to URL paths
 */
export type TabSlug = "ask" | "train" | "memory" | "settings";

export const TAB_SLUGS: TabSlug[] = ["ask", "train", "memory", "settings"];

export function isValidTabSlug(slug: string): slug is TabSlug {
  return TAB_SLUGS.includes(slug as TabSlug);
}

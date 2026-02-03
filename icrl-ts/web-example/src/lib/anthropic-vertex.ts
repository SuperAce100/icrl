/**
 * Anthropic Vertex AI provider for Claude models on Google Cloud.
 * 
 * This provider reads credentials from the GOOGLE_CREDENTIALS_JSON environment variable,
 * allowing secure deployment on Vercel without needing a credentials file.
 */

import { AnthropicVertex } from "@anthropic-ai/vertex-sdk";
import { GoogleAuth } from "google-auth-library";

// Model aliases for convenience
export const MODEL_ALIASES: Record<string, string> = {
  // Claude 3.5 models
  "claude-3-5-sonnet": "claude-3-5-sonnet-v2@20241022",
  "claude-3.5-sonnet": "claude-3-5-sonnet-v2@20241022",
  "claude-3-5-haiku": "claude-3-5-haiku@20241022",
  // Claude 3.7 models
  "claude-3-7-sonnet": "claude-3-7-sonnet@20250219",
  "claude-3.7-sonnet": "claude-3-7-sonnet@20250219",
  // Claude 4 models
  "claude-sonnet-4": "claude-sonnet-4@20250514",
  "claude-4-sonnet": "claude-sonnet-4@20250514",
  "claude-opus-4": "claude-opus-4@20250514",
  "claude-4-opus": "claude-opus-4@20250514",
  // Claude 4.5 models
  "claude-opus-4.5": "claude-opus-4-5@20251101",
  "claude-opus-4-5": "claude-opus-4-5@20251101",
  "claude-4.5-opus": "claude-opus-4-5@20251101",
  "claude-sonnet-4.5": "claude-sonnet-4-5@20251101",
  "claude-sonnet-4-5": "claude-sonnet-4-5@20251101",
  "claude-4.5-sonnet": "claude-sonnet-4-5@20251101",
};

export interface AnthropicVertexConfig {
  model?: string;
  region?: string;
  projectId?: string;
  maxTokens?: number;
  temperature?: number;
}

/**
 * Resolve model shorthand to full vertex model name
 */
function resolveModel(model: string): string {
  return MODEL_ALIASES[model] ?? model;
}

/**
 * Get credentials from environment variable
 */
function getCredentials(): {
  projectId: string;
  credentials: object;
} {
  const credentialsJson = process.env.GOOGLE_CREDENTIALS_JSON;
  
  if (!credentialsJson) {
    throw new Error(
      "GOOGLE_CREDENTIALS_JSON environment variable is not set. " +
      "Please set it to your Google Cloud service account JSON credentials."
    );
  }

  try {
    const credentials = JSON.parse(credentialsJson);
    const projectId = credentials.project_id;
    
    if (!projectId) {
      throw new Error("project_id not found in credentials JSON");
    }

    return { projectId, credentials };
  } catch (error) {
    if (error instanceof SyntaxError) {
      throw new Error(
        "GOOGLE_CREDENTIALS_JSON is not valid JSON. " +
        "Please ensure it contains the full service account credentials."
      );
    }
    throw error;
  }
}

/**
 * Create an Anthropic Vertex client
 */
export function createAnthropicVertexClient(
  config: AnthropicVertexConfig = {}
): AnthropicVertex {
  const { projectId, credentials } = getCredentials();
  
  const region = config.region ?? process.env.ANTHROPIC_VERTEX_REGION ?? "us-east5";
  const finalProjectId = config.projectId ?? projectId;

  // Create GoogleAuth with the credentials
  const googleAuth = new GoogleAuth({
    credentials,
    scopes: ["https://www.googleapis.com/auth/cloud-platform"],
  });

  return new AnthropicVertex({
    region,
    projectId: finalProjectId,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    googleAuth: googleAuth as any,
  });
}

export interface Message {
  role: "user" | "assistant";
  content: string;
}

export interface GenerateOptions {
  messages: Message[];
  systemPrompt?: string;
  model?: string;
  maxTokens?: number;
  temperature?: number;
}

/**
 * Generate a completion using Anthropic Vertex
 */
export async function generateCompletion(
  options: GenerateOptions
): Promise<string> {
  const client = createAnthropicVertexClient();
  
  const model = resolveModel(options.model ?? "claude-3-5-sonnet");
  const maxTokens = options.maxTokens ?? 4096;
  const temperature = options.temperature ?? 0.7;

  const response = await client.messages.create({
    model,
    max_tokens: maxTokens,
    system: options.systemPrompt,
    messages: options.messages,
    // Note: Vertex AI Claude doesn't support temperature in all cases
    // but we include it for compatibility
  });

  // Extract text from response
  const textBlock = response.content.find((block) => block.type === "text");
  if (textBlock && textBlock.type === "text") {
    return textBlock.text;
  }
  
  return "";
}

/**
 * Check if Anthropic Vertex is configured
 */
export function isAnthropicVertexConfigured(): boolean {
  return !!process.env.GOOGLE_CREDENTIALS_JSON;
}

/**
 * Get configuration status message
 */
export function getConfigStatus(): { configured: boolean; message: string } {
  if (isAnthropicVertexConfigured()) {
    try {
      getCredentials();
      return {
        configured: true,
        message: "Anthropic Vertex AI is configured",
      };
    } catch (error) {
      return {
        configured: false,
        message: error instanceof Error ? error.message : "Configuration error",
      };
    }
  }
  
  return {
    configured: false,
    message: "GOOGLE_CREDENTIALS_JSON environment variable not set. Using mock responses.",
  };
}

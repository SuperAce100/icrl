/**
 * Google Vertex AI Gemini provider.
 *
 * This provider reads credentials from the GOOGLE_CREDENTIALS_JSON
 * environment variable.
 */

import { GoogleAuth } from "google-auth-library";

export const MODEL_ID = "gemini-3-pro-preview";

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

export interface GeminiVertexConfig {
  model?: string;
  location?: string;
  projectId?: string;
}

interface VertexCredentials {
  projectId: string;
  credentials: object;
}

function getCredentials(): VertexCredentials {
  const credentialsJson = process.env.GOOGLE_CREDENTIALS_JSON;

  if (!credentialsJson) {
    throw new Error(
      "GOOGLE_CREDENTIALS_JSON environment variable is not set. " +
        "Please set it to your Google Cloud service account JSON credentials."
    );
  }

  try {
    const credentials = JSON.parse(credentialsJson) as {
      project_id?: string;
      [key: string]: unknown;
    };

    if (!credentials.project_id) {
      throw new Error("project_id not found in credentials JSON");
    }

    return {
      projectId: credentials.project_id,
      credentials,
    };
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

async function getAccessToken(credentials: object): Promise<string> {
  const auth = new GoogleAuth({
    credentials,
    scopes: ["https://www.googleapis.com/auth/cloud-platform"],
  });

  const token = await auth.getAccessToken();
  if (!token) {
    throw new Error("Failed to obtain Google Cloud access token.");
  }

  return token;
}

function toVertexRole(role: Message["role"]): "user" | "model" {
  return role === "assistant" ? "model" : "user";
}

/**
 * Generate a completion using Gemini on Vertex AI.
 */
export async function generateCompletion(
  options: GenerateOptions,
  config: GeminiVertexConfig = {}
): Promise<string> {
  const { projectId, credentials } = getCredentials();
  const location = config.location ?? process.env.GOOGLE_VERTEX_LOCATION ?? "global";
  const finalProjectId = config.projectId ?? projectId;
  const model = config.model ?? options.model ?? MODEL_ID;
  const maxTokens = options.maxTokens ?? 4096;
  const temperature = options.temperature ?? 0.7;

  const accessToken = await getAccessToken(credentials);

  const endpoint = `https://${location}-aiplatform.googleapis.com/v1/projects/${finalProjectId}/locations/${location}/publishers/google/models/${model}:generateContent`;

  const response = await fetch(endpoint, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify({
      contents: options.messages.map((message) => ({
        role: toVertexRole(message.role),
        parts: [{ text: message.content }],
      })),
      systemInstruction: options.systemPrompt
        ? {
            parts: [{ text: options.systemPrompt }],
          }
        : undefined,
      generationConfig: {
        temperature,
        maxOutputTokens: maxTokens,
      },
    }),
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`Vertex Gemini API error (${response.status}): ${errorBody}`);
  }

  const data = (await response.json()) as {
    candidates?: Array<{
      content?: {
        parts?: Array<{
          text?: string;
        }>;
      };
    }>;
  };

  const text = data.candidates
    ?.flatMap((candidate) => candidate.content?.parts ?? [])
    .map((part) => part.text)
    .filter((part): part is string => typeof part === "string")
    .join("\n");

  return text ?? "";
}

/**
 * Check if Gemini Vertex is configured.
 */
export function isGeminiVertexConfigured(): boolean {
  return !!process.env.GOOGLE_CREDENTIALS_JSON;
}

/**
 * Get configuration status message.
 */
export function getConfigStatus(): { configured: boolean; message: string } {
  if (isGeminiVertexConfigured()) {
    try {
      getCredentials();
      return {
        configured: true,
        message: "Google Vertex Gemini is configured",
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
    message: "GOOGLE_CREDENTIALS_JSON environment variable not set.",
  };
}

/**
 * Unified LLM provider selection for server actions.
 *
 * Selection order:
 * 1. If LLM_PROVIDER is set, use it.
 * 2. Otherwise prefer Anthropic standard API.
 * 3. Fallback to Gemini on Vertex AI.
 */

import {
  generateCompletion as generateAnthropicCompletion,
  getConfigStatus as getAnthropicConfigStatus,
  isAnthropicConfigured,
  type GenerateOptions,
} from "./anthropic";
import {
  generateCompletion as generateGeminiCompletion,
  getConfigStatus as getGeminiConfigStatus,
  isGeminiVertexConfigured,
} from "./google-vertex-gemini";

type ProviderName = "anthropic" | "gemini-vertex";

function getRequestedProvider(): ProviderName | null {
  const raw = process.env.LLM_PROVIDER?.trim().toLowerCase();
  if (!raw) {
    return null;
  }

  if (raw === "anthropic" || raw === "gemini-vertex") {
    return raw;
  }

  return null;
}

function selectProvider(): ProviderName | null {
  const requested = getRequestedProvider();
  if (requested) {
    return requested;
  }

  if (isAnthropicConfigured()) {
    return "anthropic";
  }

  if (isGeminiVertexConfigured()) {
    return "gemini-vertex";
  }

  return null;
}

export async function generateCompletion(options: GenerateOptions): Promise<string> {
  const provider = selectProvider();

  if (provider === "anthropic") {
    return generateAnthropicCompletion(options);
  }

  if (provider === "gemini-vertex") {
    return generateGeminiCompletion(options);
  }

  throw new Error(
    "No LLM provider configured. Set ANTHROPIC_API_KEY or GOOGLE_CREDENTIALS_JSON."
  );
}

export function isLlmConfigured(): boolean {
  return selectProvider() !== null;
}

export function getConfigStatus(): { configured: boolean; message: string } {
  const raw = process.env.LLM_PROVIDER?.trim().toLowerCase();
  const provider = selectProvider();

  if (raw && provider === null) {
    return {
      configured: false,
      message: `Unsupported LLM_PROVIDER value: ${raw}. Use 'anthropic' or 'gemini-vertex'.`,
    };
  }

  if (provider === "anthropic") {
    const status = getAnthropicConfigStatus();
    return {
      configured: status.configured,
      message: `Using anthropic: ${status.message}`,
    };
  }

  if (provider === "gemini-vertex") {
    const status = getGeminiConfigStatus();
    return {
      configured: status.configured,
      message: `Using gemini-vertex: ${status.message}`,
    };
  }

  return {
    configured: false,
    message:
      "No LLM provider configured. Set ANTHROPIC_API_KEY or GOOGLE_CREDENTIALS_JSON (or set LLM_PROVIDER).",
  };
}

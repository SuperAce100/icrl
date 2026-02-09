/**
 * Anthropic provider using the standard Anthropic API.
 *
 * This provider reads the API key from the ANTHROPIC_API_KEY
 * environment variable.
 */

export const MODEL_ID = "claude-opus-4-6";

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

export interface AnthropicConfig {
  apiKey?: string;
}

function getApiKey(config: AnthropicConfig = {}): string {
  const apiKey = config.apiKey ?? process.env.ANTHROPIC_API_KEY;

  if (!apiKey) {
    throw new Error(
      "ANTHROPIC_API_KEY environment variable is not set. " +
        "Please set it to your Anthropic API key."
    );
  }

  return apiKey;
}

/**
 * Generate a completion using the standard Anthropic API.
 */
export async function generateCompletion(options: GenerateOptions): Promise<string> {
  const apiKey = getApiKey();
  const model = options.model ?? process.env.ANTHROPIC_MODEL ?? MODEL_ID;
  const maxTokens = options.maxTokens ?? 4096;
  const temperature = options.temperature ?? 0.7;

  const response = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "anthropic-version": "2023-06-01",
      "x-api-key": apiKey,
    },
    body: JSON.stringify({
      model,
      max_tokens: maxTokens,
      system: options.systemPrompt,
      temperature,
      messages: options.messages,
    }),
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`Anthropic API error (${response.status}): ${errorBody}`);
  }

  const data = (await response.json()) as {
    content?: Array<{ type?: string; text?: string }>;
  };

  const text = data.content
    ?.filter((block) => block.type === "text" && typeof block.text === "string")
    .map((block) => block.text)
    .join("\n");

  return text ?? "";
}

/**
 * Check if Anthropic API is configured.
 */
export function isAnthropicConfigured(): boolean {
  return !!process.env.ANTHROPIC_API_KEY;
}

/**
 * Get configuration status message.
 */
export function getConfigStatus(): { configured: boolean; message: string } {
  if (isAnthropicConfigured()) {
    return {
      configured: true,
      message: "Anthropic API is configured",
    };
  }

  return {
    configured: false,
    message: "ANTHROPIC_API_KEY environment variable not set.",
  };
}

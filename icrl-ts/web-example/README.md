# ICRL Web Demo

An interactive web demo showing **In-Context Reinforcement Learning (ICRL)** with Human Feedback using configurable LLM providers.

## Features

- **Multi-database support**: Create and manage multiple ICRL databases
- **System prompt configuration**: Customize the AI's behavior per database
- **Human feedback loop**: Choose between generated answers or write your own
- **Persistent storage**: All data stored in Convex cloud database
- **Modern UI**: Built with shadcn/ui components and Tailwind CSS

## How It Works

1. **Ask a Question**: Type any question you want answered
2. **Retrieval**: The system searches for similar examples in the database
3. **Generation**: Two different answer options are generated using the configured LLM (influenced by retrieved examples)
4. **Human Feedback**: You choose the better answer, or write your own
5. **Learning**: Your preference is stored in the database
6. **Improvement**: Future answers are influenced by accumulated preferences

## Quick Start

### 1. Install Dependencies

```bash
pnpm install
```

### 2. Set Up Convex

Create a Convex account at [convex.dev](https://convex.dev) and initialize your project:

```bash
npx convex dev
```

This will:
- Create a Convex project
- Generate the `_generated` folder with proper types
- Give you a `NEXT_PUBLIC_CONVEX_URL` to use

### 3. Configure Environment Variables

Create a `.env.local` file with:

```env
# Convex URL (from step 2)
NEXT_PUBLIC_CONVEX_URL=https://your-deployment.convex.cloud

# Anthropic API key (default provider)
ANTHROPIC_API_KEY=sk-ant-api03-...

# Optional: force provider ("anthropic" | "gemini-vertex")
LLM_PROVIDER=anthropic

# Optional Gemini Vertex credentials (required only when using gemini-vertex)
GOOGLE_CREDENTIALS_JSON={"type":"service_account","project_id":"...","private_key":"...","client_email":"..."}

# Optional: Override Vertex AI region for Gemini (default: global)
GOOGLE_VERTEX_LOCATION=global
```

#### Getting Anthropic API Key

1. Go to [Anthropic Console](https://console.anthropic.com)
2. Create an API key
3. Set `ANTHROPIC_API_KEY` in `.env.local`

#### Getting Google Cloud Credentials (Gemini Vertex)

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create or select a project
3. Enable the Vertex AI API
4. Go to IAM & Admin > Service Accounts
5. Create a service account with Vertex AI User role
6. Create a JSON key and download it
7. Copy the entire JSON contents into `GOOGLE_CREDENTIALS_JSON`

### 4. Run Development Server

```bash
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Deployment on Vercel

### Environment Variables

Set these in your Vercel project settings:

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_CONVEX_URL` | Yes | Your Convex deployment URL |
| `ANTHROPIC_API_KEY` | Yes (default) | Anthropic API key for Claude |
| `LLM_PROVIDER` | No | Force provider: `anthropic` or `gemini-vertex` |
| `GOOGLE_CREDENTIALS_JSON` | Yes (Gemini only) | Full GCP service account JSON |
| `GOOGLE_VERTEX_LOCATION` | No | Vertex AI region (default: `global`) |

### Deploy

```bash
vercel
```

Or connect your GitHub repo for automatic deployments.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Next.js Frontend                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Database   │  │   System    │  │   Ask & Train       │  │
│  │  Selector   │  │   Prompt    │  │   Interface         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Server Actions                            │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Anthropic API (Claude) or Gemini Vertex AI         │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Convex Database                           │
│  ┌──────────────────┐  ┌──────────────────────────────┐     │
│  │  databases       │  │  examples                    │     │
│  │  - name          │  │  - question                  │     │
│  │  - systemPrompt  │  │  - chosenAnswer              │     │
│  │  - description   │  │  - rejectedAnswer            │     │
│  └──────────────────┘  │  - timesRetrieved            │     │
│                        └──────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Tech Stack

- **Framework**: Next.js 16 (App Router)
- **UI**: shadcn/ui + Tailwind CSS v4
- **Database**: Convex (real-time, serverless)
- **LLM**: Anthropic Claude (standard API) or Gemini on Vertex AI
- **Deployment**: Vercel

## Project Structure

```
web-example/
├── convex/              # Convex backend
│   ├── schema.ts        # Database schema
│   ├── databases.ts     # Database CRUD
│   └── examples.ts      # Examples CRUD
├── src/
│   ├── app/
│   │   ├── layout.tsx   # Root layout with providers
│   │   ├── page.tsx     # Main page with tabs
│   │   └── providers.tsx # Convex provider
│   ├── components/
│   │   ├── ui/          # shadcn components
│   │   ├── database-selector.tsx
│   │   ├── system-prompt-editor.tsx
│   │   ├── examples-list.tsx
│   │   ├── question-input.tsx
│   │   ├── answer-choice.tsx
│   │   └── success-message.tsx
│   └── lib/
│       ├── actions.ts   # Server actions
│       ├── anthropic.ts # Anthropic standard API provider
│       ├── google-vertex-gemini.ts # Gemini Vertex provider
│       ├── llm-provider.ts # Provider selection wrapper
│       └── utils.ts     # Utilities
└── package.json
```

## Development Notes

The app needs at least one configured LLM provider (`ANTHROPIC_API_KEY` or Gemini Vertex credentials). Without one, model-generation server actions will return a configuration error.

## License

MIT

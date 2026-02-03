# ICRL Web Demo

An interactive web demo showing **In-Context Reinforcement Learning (ICRL)** with Human Feedback using Anthropic Claude on Vertex AI.

## Features

- **Multi-database support**: Create and manage multiple ICRL databases
- **System prompt configuration**: Customize the AI's behavior per database
- **Human feedback loop**: Choose between generated answers or write your own
- **Persistent storage**: All data stored in Convex cloud database
- **Modern UI**: Built with shadcn/ui components and Tailwind CSS

## How It Works

1. **Ask a Question**: Type any question you want answered
2. **Retrieval**: The system searches for similar examples in the database
3. **Generation**: Two different answer options are generated using Claude (influenced by retrieved examples)
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

# Google Cloud credentials (paste entire JSON contents)
GOOGLE_CREDENTIALS_JSON={"type":"service_account","project_id":"...","private_key":"...","client_email":"..."}

# Optional: Override Vertex AI region (default: us-east5)
ANTHROPIC_VERTEX_REGION=us-east5
```

#### Getting Google Cloud Credentials

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
| `GOOGLE_CREDENTIALS_JSON` | Yes | Full GCP service account JSON |
| `ANTHROPIC_VERTEX_REGION` | No | Vertex AI region (default: us-east5) |

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
│  │  Anthropic Vertex AI (Claude) for answer generation │    │
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
- **LLM**: Anthropic Claude via Vertex AI
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
│       ├── anthropic-vertex.ts # LLM provider
│       └── utils.ts     # Utilities
└── package.json
```

## Development Without API Keys

The app will work without Anthropic Vertex credentials using mock responses. This is useful for:
- UI development
- Testing the Convex integration
- Demos without API costs

## License

MIT

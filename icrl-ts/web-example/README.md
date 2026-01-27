# ICRL RLHF Demo

An interactive web demo showing **Reinforcement Learning from Human Feedback (RLHF)** using the ICRL (In-Context Reinforcement Learning) system.

## How It Works

1. **Ask a Question**: Type any question you want answered
2. **Retrieval**: The system searches for similar examples in the database
3. **Generation**: Two different answer options are generated (influenced by retrieved examples)
4. **Human Feedback**: You choose the better answer, or write your own
5. **Learning**: Your preference is stored in the database
6. **Improvement**: Future answers are influenced by accumulated preferences

This demonstrates the core ICRL loop:
- **Retrieve** → Find relevant examples
- **Generate** → Create responses using examples as context
- **Feedback** → Human selects preferred output
- **Store** → Add to database for future retrieval

## Quick Start

### With Bun (Recommended)

```bash
# Install dependencies
bun install

# Set up environment
cp .env.example .env
# Edit .env and add your OpenAI API key

# Run development server
bun dev
```

### With npm

```bash
npm install
cp .env.example .env
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes* | OpenAI API key for generating answers |

*The app will work without an API key using mock responses, but real LLM-generated answers require the key.

## Features

### Ask & Train Tab
- Ask any question
- See which examples were retrieved from the database
- Choose between two generated answers
- Write your own answer if neither is good
- Feedback is immediately stored

### Database Tab
- View all stored examples
- See retrieval statistics
- Delete examples
- Track custom vs. selected answers

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Question   │→ │   Choose    │→ │  Feedback Stored    │  │
│  │   Input     │  │   Answer    │  │  (Success!)         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Server Actions                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Retrieve   │→ │  Generate   │→ │  Store Feedback     │  │
│  │  Examples   │  │  Answers    │  │  (Add to DB)        │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Example Database                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  { question, chosenAnswer, rejectedAnswer, stats }   │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Runtime**: Bun / Node.js
- **Styling**: Tailwind CSS
- **LLM**: OpenAI GPT-4o-mini
- **Database**: In-memory (demo only)

## Production Considerations

For a production deployment, you would want to:

1. **Persistent Database**: Use PostgreSQL, MongoDB, or similar
2. **Vector Store**: Use Pinecone, Weaviate, or pgvector for semantic search
3. **Embeddings**: Use OpenAI embeddings or sentence-transformers
4. **Authentication**: Add user accounts to track individual preferences
5. **Rate Limiting**: Protect API endpoints
6. **Curation**: Implement automatic pruning of low-quality examples

## Learn More

- [ICRL Documentation](https://github.com/SuperAce100/icrl)
- [Next.js Documentation](https://nextjs.org/docs)
- [OpenAI API](https://platform.openai.com/docs)

## License

MIT

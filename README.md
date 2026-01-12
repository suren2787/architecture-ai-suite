# 🏦 Digital Bank Architecture Knowledge Bot

Ever wish you had an AI assistant that actually knew your architecture docs inside and out? Well, here you go! This knowledge bot helps you quickly find answers about architecture decisions, security policies, and design standards without digging through dozens of Markdown files.

## What's This All About?

Built this to solve a real problem: our team kept asking the same questions about architecture decisions, security requirements, and design patterns. Instead of searching through ADRs and policy docs manually (or bothering the architects on Slack), I put together this RAG-powered knowledge bot that does the heavy lifting.

It's **model-agnostic** - use AWS Bedrock (DeepSeek-R1, Claude), OpenAI (GPT-4), or Anthropic, all with the same codebase.

## ✨ Features

- **Chat Interface**: Clean Streamlit UI that feels like talking to a colleague
- **Model-Agnostic**: Switch between AWS Bedrock, OpenAI, or Anthropic via config
- **Smart Retrieval**: Contextual compression with top-6 chunk retrieval from FAISS
- **Intelligent Reranking**: Prioritizes AWS, PII, DDD-related content when relevant
- **Evidence & Confidence Scores**: Every answer shows sources with similarity-based confidence (High/Medium/Low)
- **Source Citations**: Expandable evidence section with document snippets
- **Fast & Local**: Embeddings run locally, no external API calls for search
- **Live Knowledge Refresh**: Update documentation without restarting the app
- **Cost Efficient**: Only calls LLM for final answer generation

## 🏗️ Architecture

Here's how it all fits together:

```mermaid
%%{init: {'flowchart': {'curve': 'linear'}}}%%
flowchart TB
    subgraph ui["🖥️ User Interface"]
        A["Streamlit Chat UI<br/>(app.py)"]
    end
    
    subgraph rag["🧠 RAG Engine"]
        B["Brain Module<br/>(brain.py)"]
        C["FAISS Vector Store<br/>(faiss_index/)"]
        D["HuggingFace Embeddings<br/>(all-MiniLM-L6-v2)"]
    end
    
    subgraph aws["☁️ AWS Cloud"]
        E["AWS Bedrock<br/>DeepSeek-R1<br/>(us-east-1)"]
    end
    
    subgraph docs["📚 Document Store"]
        F["Markdown Docs<br/>(docs/*.md)"]
        G["Ingestion Pipeline<br/>(ingest.py)"]
    end
    
    A -->|"1. User Question"| B
    B -->|"2. Query Embedding"| D
    D -->|"3. Search Vectors"| C
    C -->|"4. Relevant Chunks"| B
    B -->|"5. Context + Question"| E
    E -->|"6. AI Response"| B
    B -->|"7. Answer + Sources"| A
    
    F -->|"Load & Split"| G
    G -->|"Create Embeddings"| D
    D -->|"Store Vectors"| C
    
    style A fill:#e1f5ff,stroke:#0288d1,stroke-width:2px
    style E fill:#fff4e1,stroke:#f57c00,stroke-width:2px
    style C fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    style B fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style D fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    style F fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    style G fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
```

**The Flow:**

1. You ask a question through the Streamlit interface
2. `brain.py` converts your question into a vector using local embeddings
3. FAISS searches the vector store for the most relevant document chunks
4. The top results get bundled with your question into a prompt
5. DeepSeek-R1 on AWS Bedrock generates a context-aware answer
6. You get the answer plus links to the source documents

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- AWS account with Bedrock access (DeepSeek-R1 enabled)
- AWS credentials configured

### Installation

1. **Clone and navigate:**
   ```bash
   cd arch-knowledge-bot
   ```

2. **Set up virtual environment:**
   ```bash
   python -m venv .venv
   .venv\Scripts\Activate.ps1  # Windows
   # or
   source .venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   
   # If using OpenAI:
   pip install openai
   
   # If using Anthropic:
   pip install anthropic
   ```

4. **Configure your LLM provider:**
   
   Copy the example environment file and configure it:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your settings. The system supports multiple LLM providers:
   
   **Option A: AWS Bedrock (Default - DeepSeek-R1)**
   ```env
   MODEL_PROVIDER=bedrock
   MODEL_NAME=us.deepseek.r1-v1:0
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_REGION=us-east-1
   ```
   
   **Option B: AWS Bedrock (Claude)**
   ```env
   MODEL_PROVIDER=bedrock
   MODEL_NAME=anthropic.claude-3-sonnet-20240229-v1:0
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_REGION=us-east-1
   ```
   
   **Option C: OpenAI**
   ```env
   MODEL_PROVIDER=openai
   MODEL_NAME=gpt-4
   OPENAI_API_KEY=sk-your-api-key-here
   ```
   
   **Option D: Anthropic**
   ```env
   MODEL_PROVIDER=anthropic
   MODEL_NAME=claude-3-opus-20240229
   ANTHROPIC_API_KEY=sk-ant-your-api-key-here
   ```

5. **Ingest your documents:**
   
   This processes all Markdown files in the `docs/` folder and creates the vector index:
   ```bash
   python ingest.py
   ```
   
   You should see something like:
   ```
   ✅ Successfully created FAISS index with 42 chunks
   ```

6. **Run the app:**
   ```bash
   streamlit run app.py
   ```
   
   The UI will open at `http://localhost:8501`

## 💬 Usage

Just type your questions in the chat! Here are some examples:

- "What are the foundational principles for microservices architecture?"
- "What's our data residency policy for Hong Kong?"
- "List all architecture decision records"
- "How should we handle authentication and authorization?"

The AI will search through your docs and give you answers with source citations. Click the "Sources" expander to see which documents were used.

## 📁 Project Structure

```
arch-knowledge-bot/
├── app.py                  # Streamlit UI
├── brain.py                # RAG logic & DeepSeek-R1 integration
├── ingest.py               # Document ingestion pipeline
├── requirements.txt        # Python dependencies
├── .env                    # AWS credentials (not committed)
├── docs/                   # Your architecture documents
│   ├── adr_fargate.md
│   ├── ADR-006-Event-Driven-Architecture.md
│   ├── security_policy.md
│   └── ...
└── faiss_index/           # Vector store (generated)
    └── index.faiss
```

## 🔧 Configuration

### LLM Provider Selection

The system is **model-agnostic** and supports multiple LLM providers. Configure via environment variables in your `.env` file:

**Environment Variables:**
- `MODEL_PROVIDER`: Choose from `bedrock`, `openai`, or `anthropic`
- `MODEL_NAME`: Specify the model ID/name for your chosen provider

**Supported Models:**

| Provider | MODEL_NAME Examples | Additional Config Required |
|----------|-------------------|---------------------------|
| **AWS Bedrock** | `us.deepseek.r1-v1:0`<br>`anthropic.claude-3-sonnet-20240229-v1:0`<br>`anthropic.claude-v2` | `AWS_ACCESS_KEY_ID`<br>`AWS_SECRET_ACCESS_KEY`<br>`AWS_REGION` |
| **OpenAI** | `gpt-4`<br>`gpt-4-turbo`<br>`gpt-3.5-turbo` | `OPENAI_API_KEY` |
| **Anthropic** | `claude-3-opus-20240229`<br>`claude-3-sonnet-20240229` | `ANTHROPIC_API_KEY` |

The UI will automatically display which provider and model are currently active.

### Embeddings Model

Currently using `sentence-transformers/all-MiniLM-L6-v2` which runs locally. It's fast and good enough for most use cases. If you want better accuracy, you can swap it for a larger model in both `ingest.py` and `brain.py`.

### Chunk Size

Documents are split into 1000-character chunks with 200-character overlap. Tune these in `ingest.py` if you're working with different doc types:

```python
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)
```

### LLM Parameters

In `brain.py`, you can adjust the LLM parameters (works across all providers):

```python
invoke_llm(
    prompt,
    max_tokens=1024,      # Increase for longer answers
    temperature=0.7,      # Lower for more focused answers
    top_p=0.9
)
```

## 📝 Adding New Documents

1. Drop your Markdown files into the `docs/` folder
2. Re-run the ingestion:
   ```bash
   python ingest.py
   ```
3. Restart the Streamlit app

That's it! The new docs will be searchable immediately.

## 🤔 Troubleshooting

**"FAISS index not found"**
- Run `python ingest.py` first to create the index

**AWS Bedrock errors**
- Check your `.env` file has valid credentials
- Verify DeepSeek-R1 is enabled in your AWS region (us-east-1)
- Make sure you have Bedrock permissions

**Embeddings model download hangs**
- First run downloads the model (~80MB), be patient
- Check your internet connection
- Model gets cached in `~/.cache/huggingface/`

**Answers seem off**
- Try rephrasing your question
- Check if the relevant docs are in the `docs/` folder
- Increase `k` value in `brain.py` to retrieve more context chunks

## 🛠️ Tech Stack

- **UI**: Streamlit
- **Vector Store**: FAISS (CPU-based, local)
- **Embeddings**: HuggingFace Transformers (all-MiniLM-L6-v2)
- **LLM**: Model-agnostic (supports AWS Bedrock, OpenAI, Anthropic)
- **Framework**: LangChain

## 💡 Future Ideas

Some things I'm thinking about adding:

- [ ] Support for PDF and DOCX files
- [ ] Conversation memory (multi-turn Q&A)
- [ ] Admin panel to manage docs
- [ ] Export chat history
- [ ] Support for other LLMs (Claude, GPT-4, etc.)
- [ ] Docker containerization

## 📄 License

Do whatever you want with this. If it helps your team, that's awesome!

---

Built with ☕ and mild frustration at having to search through docs manually.

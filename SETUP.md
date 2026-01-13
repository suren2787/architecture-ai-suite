# Architecture AI Suite - Setup Guide

This guide will help you set up the Architecture AI Suite from scratch.

## Prerequisites

- Python 3.8 or higher
- Access to one of the following LLM providers:
  - AWS Bedrock (with DeepSeek-R1, Claude, or other models)
  - OpenAI API
  - Anthropic API
- (Optional) Confluence API access for knowledge base sync

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example files and edit them with your credentials:

```bash
cp .env.example .env
cp config.env.example config.env
```

#### Edit `.env` for LLM/API Configuration

Choose your LLM provider and add credentials:

**For AWS Bedrock (Default):**
```bash
MODEL_PROVIDER=bedrock
MODEL_NAME=us.deepseek.r1-v1:0
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=us-east-1

# Embeddings (Bedrock Titan)
EMBEDDING_PROVIDER=bedrock
EMBEDDING_MODEL=amazon.titan-embed-text-v2:0
```

**For OpenAI:**
```bash
MODEL_PROVIDER=openai
MODEL_NAME=gpt-4
OPENAI_API_KEY=your_openai_api_key_here

# Embeddings
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
```

**For Anthropic:**
```bash
MODEL_PROVIDER=anthropic
MODEL_NAME=claude-3-opus-20240229
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

**Optional - Confluence Integration:**
```bash
CONFLUENCE_EMAIL=your-email@company.com
CONFLUENCE_API_TOKEN=your_confluence_api_token
CONFLUENCE_BASE_URL=https://yourcompany.atlassian.net/wiki
```

#### Edit `config.env` for Organization Settings

Customize for your organization:

```bash
# Branding
ORGANIZATION_NAME=Your Company
ORGANIZATION_ICON=🏢

# Priority ADRs (comma-separated)
PRIORITY_ADRS=ADR-007,ADR-008

# Reranking keywords for search boost
RERANKING_KEYWORDS=aws,pii,gdpr,kubernetes,microservices

# Audit aspects to check
AUDIT_ASPECTS=Data Storage,Authentication,Authorization,Security,Compliance

# Confluence sync (optional)
CONFLUENCE_SPACE_KEY=ARCH
CONFLUENCE_LABELS=adr,standards
```

### 3. Build the Knowledge Base

The repository comes with sample ADRs and standards in the `docs/` folder. Create the FAISS index:

```bash
python ingest.py
```

You should see output like:
```
Loading Markdown files from: /path/to/docs
Loaded 7 documents
Splitting documents into chunks...
Created 45 chunks
✅ Successfully created FAISS index with 45 chunks
```

### 4. Launch the Application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Testing Your Setup

### Test 1: Verify Embeddings

```bash
python test_embeddings.py
```

Expected output:
```
✅ BEDROCK embeddings working!
   Model: amazon.titan-embed-text-v2:0
   Dimension: 1024
```

### Test 2: Test Knowledge Bot (Terminal)

```bash
python brain.py
```

This will run a sample query against the knowledge base.

### Test 3: Test Solution Auditor (Terminal)

```bash
python reviewer.py
```

This will run a sample audit on the example e-commerce design.

### Test 4: Generate Sample Audit Report

```bash
python generate_sample_audit.py
```

Check `samples/sample_audit_report.md` for the output.

## Adding Your Own Documents

### Option 1: Local Files

1. Add Markdown files to the `docs/` folder
2. Run `python ingest.py` to rebuild the FAISS index
3. Restart the Streamlit app

### Option 2: Confluence Sync

1. Configure Confluence in `.env` (email, token, base URL)
2. Set `CONFLUENCE_SPACE_KEY` in `config.env`
3. Use the "Sync from Confluence" button in the app sidebar

## Troubleshooting

### "ModuleNotFoundError: No module named 'streamlit'"

**Solution:** Install dependencies:
```bash
pip install -r requirements.txt
```

### "FAISS index not found"

**Solution:** Build the index:
```bash
python ingest.py
```

### "Authentication failed" (AWS Bedrock)

**Checklist:**
- Verify AWS credentials in `.env`
- Ensure AWS region is correct (e.g., `us-east-1`)
- Verify Bedrock access is enabled in your AWS account
- Check that the model is available in your region

### "Authentication failed" (Confluence)

**Checklist:**
- Verify `CONFLUENCE_EMAIL` and `CONFLUENCE_API_TOKEN` in `.env`
- Create a Confluence API token: https://id.atlassian.com/manage-profile/security/api-tokens
- Ensure you have read access to the Confluence space

### Answers seem irrelevant or wrong

**Solutions:**
- Add more relevant documents to the `docs/` folder
- Adjust `RERANKING_KEYWORDS` in `config.env` for your domain
- Increase `k` parameter in `brain.py` (line 242) to retrieve more chunks
- Try rephrasing your question

## Architecture

```
architecture-ai-suite/
├── app.py                      # Streamlit UI
├── brain.py                    # RAG engine (FAISS + LLM)
├── reviewer.py                 # Solution auditor
├── ingest.py                   # Document ingestion
├── embeddings.py               # Model-agnostic embeddings
├── config.py                   # Config loader
├── confluence.py               # Single page fetcher
├── confluence_sync.py          # Bulk space sync
├── docs/                       # Knowledge base documents
│   ├── ADR-*.md               # Architecture Decision Records
│   ├── ea_standards.md        # Enterprise Architecture standards
│   └── security_policy.md     # Security policies
├── faiss_index/               # Vector store (auto-generated)
├── samples/                    # Example outputs
├── .env.example               # API credentials template
└── config.env.example         # Organization settings template
```

## Next Steps

1. **Customize for your organization:**
   - Update `config.env` with your company name and standards
   - Replace sample ADRs in `docs/` with your actual decision records

2. **Integrate with Confluence:**
   - Set up Confluence sync to pull your existing ADRs automatically
   - Use labels to filter relevant pages

3. **Train your team:**
   - Share example queries in the Knowledge Bot
   - Run sample audits to demonstrate the Solution Auditor

4. **Extend functionality:**
   - Add custom audit aspects in `config.env`
   - Integrate with CI/CD pipelines for automated design reviews
   - Export audit reports to Confluence

## Security Considerations

- **Never commit `.env` or `config.env`** - they are git-ignored by default
- Store API keys in environment variables or secrets management
- The FAISS index is committed by default (contains only embeddings of your docs)
- If your ADRs contain sensitive info, uncomment `faiss_index/` in `.gitignore`

## Getting Help

- Check the main [README.md](README.md) for architecture overview
- Review `samples/` folder for example outputs
- Examine the code modules for implementation details

## License

MIT - Use freely for your organization.

# OpenWebUI Setup Guide

This guide explains how to configure the Architecture AI Suite to use OpenWebUI as a proxy to Bedrock or other LLM providers, for environments where direct AWS Bedrock access is not available.

## What is OpenWebUI?

OpenWebUI is an open-source web interface for LLMs that can act as a proxy to various LLM providers including AWS Bedrock, OpenAI, and others. It provides an OpenAI-compatible API, making it easy to integrate with applications.

## Why Use OpenWebUI?

- **No Direct AWS Access Required**: If your environment restricts direct AWS Bedrock API calls, OpenWebUI can act as a proxy
- **Centralized API Management**: Manage all your LLM access through a single OpenWebUI instance
- **Unified Interface**: Use the same OpenAI-compatible API for multiple backend providers
- **Access Control**: OpenWebUI provides its own authentication and authorization layer

## Prerequisites

1. **OpenWebUI Instance**: You need access to an OpenWebUI instance (either hosted or self-hosted)
2. **API Key**: Generate an API key from your OpenWebUI instance
3. **Model Access**: Ensure the models you want to use are configured in OpenWebUI

## Configuration Steps

### Step 1: Get OpenWebUI Credentials

1. Log into your OpenWebUI instance
2. Navigate to **Settings** → **Account** → **API Keys**
3. Click **Generate New API Key**
4. Copy the generated API key (you won't be able to see it again)
5. Note your OpenWebUI instance URL (e.g., `https://openwebui.yourcompany.com`)

### Step 2: Configure Environment Variables

Edit your `.env` file and add the following:

```env
# ===================================================================
# LLM Provider Configuration
# ===================================================================
MODEL_PROVIDER=openwebui
MODEL_NAME=deepseek-r1  # or your preferred model available in OpenWebUI

# ===================================================================
# OpenWebUI Configuration
# ===================================================================
OPENWEBUI_API_KEY=your-api-key-here
OPENWEBUI_BASE_URL=https://your-openwebui-instance.com/api/v1

# ===================================================================
# Embeddings Configuration (Optional - can also use OpenWebUI)
# ===================================================================
EMBEDDING_PROVIDER=openwebui
EMBEDDING_MODEL=text-embedding-3-small  # or any embedding model in OpenWebUI
```

### Step 3: Verify Available Models

Check which models are available in your OpenWebUI instance:

```bash
# Using curl to list available models
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://your-openwebui-instance.com/api/v1/models
```

Or check in the OpenWebUI web interface under the model selection dropdown.

### Step 4: Test the Configuration

Test the LLM connection:

```bash
# Activate your virtual environment first
source .venv/bin/activate  # On Mac/Linux
# or
.venv\Scripts\Activate.ps1  # On Windows

# Test the LLM
python -c "from brain import invoke_llm; print(invoke_llm('Hello, this is a test.'))"
```

Test the embeddings:

```bash
python -c "from embeddings import test_embeddings; test_embeddings()"
```

### Step 5: Run the Application

```bash
streamlit run app.py
```

The application should now use OpenWebUI as the proxy for all LLM and embedding calls.

## Configuration Examples

### Example 1: OpenWebUI with Bedrock Models (via proxy)

```env
MODEL_PROVIDER=openwebui
MODEL_NAME=deepseek-r1  # Bedrock DeepSeek-R1 via OpenWebUI
OPENWEBUI_API_KEY=owui_abc123xyz
OPENWEBUI_BASE_URL=https://openwebui.company.com/api/v1

EMBEDDING_PROVIDER=openwebui
EMBEDDING_MODEL=amazon.titan-embed-text-v2:0
```

### Example 2: OpenWebUI with Mixed Providers

```env
# Use OpenWebUI for LLM
MODEL_PROVIDER=openwebui
MODEL_NAME=claude-3-sonnet
OPENWEBUI_API_KEY=owui_abc123xyz
OPENWEBUI_BASE_URL=https://openwebui.company.com/api/v1

# Use local HuggingFace for embeddings
EMBEDDING_PROVIDER=huggingface
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### Example 3: Fallback to Bedrock

If you have direct AWS access in some environments and OpenWebUI in others, you can switch by changing just the `MODEL_PROVIDER`:

```env
# Development (with AWS access)
MODEL_PROVIDER=bedrock
MODEL_NAME=us.deepseek.r1-v1:0
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...

# Production (via OpenWebUI proxy)
MODEL_PROVIDER=openwebui
MODEL_NAME=deepseek-r1
OPENWEBUI_API_KEY=...
OPENWEBUI_BASE_URL=...
```

## Troubleshooting

### Error: "OPENWEBUI_API_KEY not set in environment variables"

**Solution**: Ensure your `.env` file contains `OPENWEBUI_API_KEY=your-key`

### Error: "OPENWEBUI_BASE_URL not set in environment variables"

**Solution**: Add `OPENWEBUI_BASE_URL=https://your-instance.com/api/v1` to `.env`

**Important**: The URL should end with `/api/v1` for OpenAI-compatible endpoints

### Error: Connection timeout or refused

**Possible causes**:
- OpenWebUI instance is down
- Incorrect URL
- Network/firewall blocking the connection

**Solution**:
```bash
# Test connectivity
curl -v https://your-openwebui-instance.com/api/v1/models
```

### Error: 401 Unauthorized

**Possible causes**:
- Invalid API key
- Expired API key
- API key doesn't have required permissions

**Solution**:
- Generate a new API key from OpenWebUI
- Verify the key is correctly copied to `.env`

### Error: Model not found

**Possible causes**:
- Model name doesn't match what's available in OpenWebUI
- Model not configured in your OpenWebUI instance

**Solution**:
```bash
# List available models
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://your-openwebui-instance.com/api/v1/models

# Update MODEL_NAME in .env to match an available model
```

### Wrong responses or unexpected behavior

**Check**:
1. Model name is correct
2. OpenWebUI is properly proxying to the backend (Bedrock/OpenAI/etc.)
3. Test the same prompt directly in OpenWebUI web interface

## Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│         Architecture AI Suite                   │
│  ┌──────────────┐         ┌─────────────┐      │
│  │  Streamlit   │────────▶│   brain.py  │      │
│  │     App      │         │             │      │
│  └──────────────┘         └─────────────┘      │
│                                   │             │
│                                   ▼             │
└───────────────────────────────────┼─────────────┘
                                    │
                    HTTPS API Call  │
                                    │
                                    ▼
┌─────────────────────────────────────────────────┐
│              OpenWebUI Instance                  │
│         (OpenAI-compatible API)                 │
│  ┌──────────────┐                               │
│  │ API Gateway  │                               │
│  └──────────────┘                               │
│         │                                        │
│         ▼                                        │
│  ┌──────────────────────────────────┐          │
│  │    Model Router / Proxy          │          │
│  └──────────────────────────────────┘          │
└─────────────────────┬───────────────────────────┘
                      │
        ┌─────────────┴──────────────┐
        ▼                            ▼
┌──────────────┐            ┌──────────────┐
│ AWS Bedrock  │            │ Other LLMs   │
│  DeepSeek    │            │ (OpenAI,     │
│  Claude      │            │  Claude, etc)│
└──────────────┘            └──────────────┘
```

## Security Considerations

1. **API Key Storage**: Store your `OPENWEBUI_API_KEY` securely in `.env` (never commit to git)
2. **HTTPS**: Always use HTTPS for `OPENWEBUI_BASE_URL`
3. **Network Security**: Ensure communication between your app and OpenWebUI is encrypted
4. **Access Control**: Use OpenWebUI's built-in access controls to limit which models users can access

## Performance Considerations

- **Latency**: There's an additional network hop through OpenWebUI, which may add 50-200ms latency
- **Rate Limiting**: Check OpenWebUI's rate limits and configure accordingly
- **Caching**: OpenWebUI may cache responses for identical queries (check your instance configuration)

## Migration from Direct Bedrock

If you're migrating from direct Bedrock access to OpenWebUI:

1. **Keep old config as backup**:
   ```bash
   cp .env .env.bedrock.backup
   ```

2. **Update MODEL_PROVIDER**:
   ```env
   # Old
   MODEL_PROVIDER=bedrock
   
   # New
   MODEL_PROVIDER=openwebui
   ```

3. **Map model names**:
   - Bedrock: `us.deepseek.r1-v1:0` → OpenWebUI: `deepseek-r1`
   - Bedrock: `anthropic.claude-3-sonnet-20240229-v1:0` → OpenWebUI: `claude-3-sonnet`

4. **Test thoroughly** before switching production workloads

5. **No code changes required** - only configuration updates needed!

## Support

If you encounter issues not covered here:

1. Check OpenWebUI documentation: https://docs.openwebui.com
2. Verify your OpenWebUI instance is working (test with curl or web interface)
3. Check application logs for detailed error messages
4. Review the `.env` configuration for typos

## Additional Resources

- [OpenWebUI Documentation](https://docs.openwebui.com)
- [OpenWebUI GitHub Repository](https://github.com/open-webui/open-webui)
- [OpenAI API Compatibility](https://platform.openai.com/docs/api-reference)

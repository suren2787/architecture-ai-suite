# Migration Guide: AWS Bedrock to OpenWebUI

This guide helps you migrate from direct AWS Bedrock access to using OpenWebUI as a proxy.

## Why Migrate to OpenWebUI?

- **No Direct AWS Access**: Some environments restrict direct AWS API access
- **Centralized Management**: Manage all LLM access through a single OpenWebUI instance
- **Unified Interface**: Use the same API for multiple LLM providers
- **Access Control**: Additional authentication and authorization layer

## Configuration Comparison

### Before (Direct AWS Bedrock)

```env
# .env file
MODEL_PROVIDER=bedrock
MODEL_NAME=us.deepseek.r1-v1:0
AWS_ACCESS_KEY_ID=AKIAXXXXXXXXXXXXXXXX
AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
AWS_REGION=us-east-1

EMBEDDING_PROVIDER=bedrock
EMBEDDING_MODEL=amazon.titan-embed-text-v2:0
```

### After (OpenWebUI Proxy)

```env
# .env file
MODEL_PROVIDER=openwebui
MODEL_NAME=deepseek-r1
OPENWEBUI_API_KEY=owui_xxxxxxxxxxxxxxxx
OPENWEBUI_BASE_URL=https://openwebui.company.com/api/v1

EMBEDDING_PROVIDER=openwebui
EMBEDDING_MODEL=text-embedding-3-small
```

## Model Name Mapping

When migrating, you'll need to map AWS Bedrock model IDs to OpenWebUI model names:

| AWS Bedrock Model ID | OpenWebUI Model Name | Notes |
|---------------------|---------------------|-------|
| `us.deepseek.r1-v1:0` | `deepseek-r1` | Simplified name |
| `anthropic.claude-3-sonnet-20240229-v1:0` | `claude-3-sonnet` | Version may vary |
| `anthropic.claude-v2` | `claude-v2` | Legacy Claude |
| `amazon.titan-embed-text-v2:0` | `amazon-titan-embed-v2` | Embedding model |

**Important**: The exact model names in OpenWebUI depend on how your administrator configured the instance. Always check your OpenWebUI instance for available models.

## Step-by-Step Migration

### Step 1: Backup Current Configuration

```bash
# Backup your current .env file
cp .env .env.bedrock.backup
```

### Step 2: Get OpenWebUI Credentials

1. Access your OpenWebUI instance
2. Navigate to **Settings** → **Account** → **API Keys**
3. Generate a new API key
4. Note the API key and base URL

### Step 3: Update .env File

You can either:

**Option A: Start from template**
```bash
cp .env.openwebui.example .env
# Then edit .env with your credentials
```

**Option B: Manually update existing .env**
```env
# Change these lines:
MODEL_PROVIDER=openwebui           # was: bedrock
MODEL_NAME=deepseek-r1             # was: us.deepseek.r1-v1:0

# Add these new lines:
OPENWEBUI_API_KEY=your-api-key-here
OPENWEBUI_BASE_URL=https://your-instance.com/api/v1

# Remove or comment out AWS credentials (no longer needed):
# AWS_ACCESS_KEY_ID=...
# AWS_SECRET_ACCESS_KEY=...
# AWS_REGION=...

# Update embeddings (optional):
EMBEDDING_PROVIDER=openwebui       # was: bedrock
EMBEDDING_MODEL=text-embedding-3-small  # was: amazon.titan-embed-text-v2:0
```

### Step 4: Test Configuration

```bash
# Run the test script
python test_openwebui.py
```

Expected output:
```
============================================================
  Testing OpenWebUI LLM Connection
============================================================
✓ API Key: owui_abc12...xyz9
✓ Base URL: https://openwebui.company.com/api/v1
✓ Model: deepseek-r1

Testing LLM inference...
✅ LLM Response: Hello, OpenWebUI is working!

✅ OpenWebUI LLM connection is working!

============================================================
  Testing OpenWebUI Embeddings Connection
============================================================
...
✅ All tests passed!

You're ready to run the application:
  streamlit run app.py
```

### Step 5: Run the Application

```bash
streamlit run app.py
```

Check the sidebar to verify it shows:
- **Provider:** OPENWEBUI (Proxy)
- **Endpoint:** https://your-instance.com/api/v1
- **Model:** DeepSeek-R1

### Step 6: Verify Functionality

Test the following features:

1. **Knowledge Bot**:
   - Ask a question: "What is our data residency policy?"
   - Verify you get a response with sources

2. **Solution Auditor**:
   - Submit a test design document
   - Verify the audit runs and produces results

3. **Confluence Sync** (if configured):
   - Click "Sync from Confluence"
   - Verify pages are synced

## Troubleshooting Migration Issues

### Issue: "OPENWEBUI_API_KEY not set in environment variables"

**Solution**: Make sure your `.env` file contains:
```env
OPENWEBUI_API_KEY=your-actual-key-here
```

### Issue: "Connection timeout" or "Connection refused"

**Possible causes**:
- OpenWebUI instance is down
- Incorrect URL
- Network/firewall blocking connection

**Solution**:
```bash
# Test connectivity
curl https://your-openwebui-instance.com/api/v1/models

# If this fails, check:
# 1. Is the URL correct?
# 2. Is OpenWebUI running?
# 3. Can you access it from a browser?
```

### Issue: "Model not found"

**Possible causes**:
- Model name doesn't match what's in OpenWebUI
- Model not configured in OpenWebUI

**Solution**:
```bash
# List available models
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://your-instance.com/api/v1/models

# Update MODEL_NAME in .env to match an available model
```

### Issue: Different responses than Bedrock

**Explanation**: OpenWebUI might have different default parameters or the model might behave slightly differently through the proxy.

**Solution**:
- Review your OpenWebUI configuration
- Check temperature and other parameters
- Test the same prompt in both environments

### Issue: Slower performance

**Explanation**: There's an additional network hop through OpenWebUI.

**Expected impact**: 50-200ms additional latency per request

**Mitigation**:
- Ensure OpenWebUI is geographically close to your application
- Check OpenWebUI instance performance
- Consider caching strategies for frequent queries

## Rollback Plan

If you need to rollback to direct Bedrock access:

```bash
# Restore your backup
cp .env.bedrock.backup .env

# Restart the application
streamlit run app.py
```

## Performance Comparison

| Aspect | Direct Bedrock | Via OpenWebUI |
|--------|---------------|---------------|
| **Latency** | Lower (direct) | Higher (+50-200ms) |
| **Setup** | Requires AWS credentials | Requires OpenWebUI credentials |
| **Access Control** | AWS IAM | OpenWebUI + AWS IAM |
| **Monitoring** | CloudWatch | OpenWebUI + CloudWatch |
| **Cost** | Direct AWS billing | Depends on OpenWebUI setup |

## Code Changes Required

**Good news**: ✅ **No code changes required!**

The application is designed to be provider-agnostic. Only configuration changes are needed:
- ✅ All LLM calls use the same `invoke_llm()` function
- ✅ All embedding calls use the same `get_embeddings()` function
- ✅ Provider is selected via environment variables
- ✅ No need to modify any Python files

## Testing Checklist

Before considering migration complete:

- [ ] Test script passes: `python test_openwebui.py`
- [ ] Application starts: `streamlit run app.py`
- [ ] Knowledge Bot responds to questions
- [ ] Solution Auditor processes design documents
- [ ] Sources are correctly displayed
- [ ] Embeddings work (FAISS index loads)
- [ ] Confluence sync works (if used)
- [ ] Performance is acceptable
- [ ] All team members have OpenWebUI access

## Best Practices

1. **Keep Both Configurations**: Maintain both `.env.bedrock.backup` and `.env` for easy switching
2. **Document the Change**: Update your team's documentation about which environment uses which configuration
3. **Monitor Performance**: Track response times before and after migration
4. **Test Thoroughly**: Test all features before switching production
5. **Gradual Rollout**: Consider switching dev/staging environments first

## Getting Help

If you encounter issues during migration:

1. ✅ Check this migration guide
2. ✅ Review [docs/OPENWEBUI_SETUP.md](OPENWEBUI_SETUP.md)
3. ✅ Run `python test_openwebui.py` for diagnostics
4. ✅ Check OpenWebUI documentation
5. ✅ Verify OpenWebUI instance is working (test in web interface)
6. ✅ Review application logs for detailed error messages

## Summary

Migration from AWS Bedrock to OpenWebUI is **configuration-only** and requires:

1. ✅ New environment variables (OPENWEBUI_API_KEY, OPENWEBUI_BASE_URL)
2. ✅ Updated MODEL_PROVIDER and MODEL_NAME
3. ✅ No code changes
4. ✅ Testing with provided test script

The same codebase works with both providers, making it easy to switch back if needed.

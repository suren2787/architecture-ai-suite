import boto3
import json
import os
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from embeddings import get_embeddings
import config

# Load environment variables from .env file
load_dotenv()

# Global variable to store the loaded FAISS index
_vectorstore = None

def load_faiss_index(index_path=None):
    """
    Load the FAISS index from local storage.
    
    Args:
        index_path (str, optional): Path to the FAISS index folder. 
                                   Defaults to 'faiss_index' in the script directory.
    
    Returns:
        FAISS: The loaded FAISS vectorstore
    """
    global _vectorstore
    
    if _vectorstore is not None:
        return _vectorstore
    
    if index_path is None:
        index_path = os.path.join(os.path.dirname(__file__), 'faiss_index')
    
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"FAISS index not found at: {index_path}. Please run ingest.py first.")
    
    # Initialize embeddings using configured provider
    embeddings = get_embeddings()
    
    # Load the FAISS index
    _vectorstore = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
    
    return _vectorstore

def invoke_llm(prompt, max_tokens=1024, temperature=0.7, top_p=0.9):
    """
    Invoke LLM based on configured provider (model-agnostic).
    
    Supports:
    - AWS Bedrock (DeepSeek-R1, Claude, etc.)
    - OpenAI (GPT-4, GPT-3.5, etc.)
    - Anthropic (Claude via API)
    - OpenWebUI (Proxy to Bedrock or other models)
    
    Configuration via environment variables:
    - MODEL_PROVIDER: 'bedrock', 'openai', 'anthropic', or 'openwebui'
    - MODEL_NAME: specific model ID/name
    
    Args:
        prompt (str): The prompt to send to the LLM
        max_tokens (int, optional): Maximum tokens to generate. Defaults to 1024
        temperature (float, optional): Sampling temperature. Defaults to 0.7
        top_p (float, optional): Nucleus sampling parameter. Defaults to 0.9
        
    Returns:
        str: The response from the LLM
    """
    provider = os.getenv('MODEL_PROVIDER', 'bedrock').lower()
    model_name = os.getenv('MODEL_NAME', 'us.deepseek.r1-v1:0')
    
    if provider == 'bedrock':
        return _invoke_bedrock(prompt, model_name, max_tokens, temperature, top_p)
    elif provider == 'openai':
        return _invoke_openai(prompt, model_name, max_tokens, temperature, top_p)
    elif provider == 'anthropic':
        return _invoke_anthropic(prompt, model_name, max_tokens, temperature, top_p)
    elif provider == 'openwebui':
        return _invoke_openwebui(prompt, model_name, max_tokens, temperature, top_p)
    else:
        raise ValueError(f"Unsupported MODEL_PROVIDER: {provider}. Use 'bedrock', 'openai', 'anthropic', or 'openwebui'.")

def _invoke_bedrock(prompt, model_id, max_tokens=1024, temperature=0.7, top_p=0.9):
    """Invoke AWS Bedrock models (DeepSeek-R1, Claude, etc.)"""
    region_name = os.getenv('AWS_REGION', 'us-east-1')
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    
    # Create a Bedrock runtime client
    client_kwargs = {'region_name': region_name}
    if aws_access_key and aws_secret_key:
        client_kwargs['aws_access_key_id'] = aws_access_key
        client_kwargs['aws_secret_access_key'] = aws_secret_key
    
    bedrock_runtime = boto3.client('bedrock-runtime', **client_kwargs)
    
    # Handle different Bedrock model formats
    if 'deepseek' in model_id.lower():
        # DeepSeek-R1 format
        body = json.dumps({
            'prompt': prompt,
            'max_tokens': max_tokens,
            'temperature': temperature,
            'top_p': top_p
        })
    elif 'claude' in model_id.lower():
        # Claude format
        body = json.dumps({
            'prompt': f"\n\nHuman: {prompt}\n\nAssistant:",
            'max_tokens_to_sample': max_tokens,
            'temperature': temperature,
            'top_p': top_p
        })
    else:
        # Generic format
        body = json.dumps({
            'prompt': prompt,
            'max_tokens': max_tokens,
            'temperature': temperature,
            'top_p': top_p
        })
    
    # Invoke the model
    response = bedrock_runtime.invoke_model(
        modelId=model_id,
        body=body,
        accept='application/json',
        contentType='application/json'
    )
    
    # Parse the response
    response_body = json.loads(response['body'].read().decode('utf-8'))
    
    # Extract text based on model type
    if 'choices' in response_body:
        return response_body['choices'][0]['text']
    elif 'completion' in response_body:
        return response_body['completion']
    else:
        return "No response content found"

def _invoke_openai(prompt, model_name, max_tokens=1024, temperature=0.7, top_p=0.9):
    """Invoke OpenAI models (GPT-4, GPT-3.5, etc.)"""
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("OpenAI package not installed. Run: pip install openai")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set in environment variables")
    
    client = OpenAI(api_key=api_key)
    
    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p
    )
    
    return response.choices[0].message.content

def _invoke_anthropic(prompt, model_name, max_tokens=1024, temperature=0.7, top_p=0.9):
    """Invoke Anthropic Claude models via API"""
    try:
        from anthropic import Anthropic
    except ImportError:
        raise ImportError("Anthropic package not installed. Run: pip install anthropic")
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set in environment variables")
    
    client = Anthropic(api_key=api_key)
    
    response = client.messages.create(
        model=model_name,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text

def _invoke_openwebui(prompt, model_name, max_tokens=1024, temperature=0.7, top_p=0.9):
    """Invoke OpenWebUI API (OpenAI-compatible proxy to Bedrock or other models)"""
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("OpenAI package not installed. Run: pip install openai")
    
    api_key = os.getenv('OPENWEBUI_API_KEY')
    base_url = os.getenv('OPENWEBUI_BASE_URL')
    
    if not api_key:
        raise ValueError("OPENWEBUI_API_KEY not set in environment variables")
    if not base_url:
        raise ValueError("OPENWEBUI_BASE_URL not set in environment variables")
    
    # Initialize OpenAI client with OpenWebUI endpoint
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
    
    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p
    )
    
    return response.choices[0].message.content

# Backward compatibility alias
def invoke_deepseek_r1(prompt, region_name=None, max_tokens=1024, temperature=0.7, top_p=0.9):
    """
    Deprecated: Use invoke_llm() instead.
    Kept for backward compatibility.
    """
    return invoke_llm(prompt, max_tokens, temperature, top_p)

def rerank_chunks(docs, question):
    """
    Rerank retrieved chunks to prioritize those mentioning configured keywords if relevant to the query.
    
    Args:
        docs (list): List of Document objects from FAISS
        question (str): The user's question
    
    Returns:
        list: Reranked list of documents
    """
    # Get priority keywords from config
    priority_keywords = config.RERANKING_KEYWORDS
    question_lower = question.lower()
    
    # Check if question mentions any priority keywords
    query_has_priority = any(kw in question_lower for kw in priority_keywords)
    
    if not query_has_priority:
        return docs  # No reranking needed
    
    # Score each document
    scored_docs = []
    for doc in docs:
        content_lower = doc.page_content.lower()
        score = 0
        
        # Boost score if document contains priority keywords
        for kw in priority_keywords:
            if kw in content_lower:
                score += content_lower.count(kw)
        
        scored_docs.append((score, doc))
    
    # Sort by score (descending) and return documents
    scored_docs.sort(key=lambda x: x[0], reverse=True)
    return [doc for score, doc in scored_docs]

def ask_auditor(question):
    """
    Ask a question to the AI architect auditor using the FAISS index and DeepSeek-R1.
    Uses contextual compression and reranking for better retrieval.
    
    Args:
        question (str): The question to ask
    
    Returns:
        tuple[str, list[dict]]: The response from DeepSeek-R1, and a list of sources with
        filename, content, and confidence score for each retrieved chunk.
    """
    # Load FAISS index if not already loaded
    vectorstore = load_faiss_index()
    
    # Retrieve top 6 chunks from FAISS with similarity scores (contextual compression approach)
    # Use k=10 for listing questions, otherwise 6 for better context
    k = 10 if any(word in question.lower() for word in ["list", "all", "show", "enumerate"]) else 6
    docs_with_scores = vectorstore.similarity_search_with_score(question, k=k)
    
    # Extract documents and scores
    relevant_docs = [doc for doc, score in docs_with_scores]
    
    # Apply reranking to prioritize AWS, PII, DDD-related chunks
    relevant_docs = rerank_chunks(relevant_docs, question)
    
    # Prepare context and source metadata with confidence scores
    context = "\n\n".join([doc.page_content for doc in relevant_docs])
    sources = []
    
    # FAISS similarity_search_with_score returns L2 (Euclidean) distance by default
    # Lower distance = better match (more similar vectors)
    # Typical range for normalized embeddings: 0.0 (identical) to 2.0 (very different)
    # 
    # Confidence score calculation based on FAISS distance metrics:
    # - Distance < 0.8: High confidence (very similar semantic meaning)
    # - Distance 0.8-1.5: Medium confidence (related content)
    # - Distance > 1.5: Low confidence (potentially tangential)
    #
    # Note: These thresholds are calibrated for Titan embeddings (1024-dim, normalized)
    
    for doc in relevant_docs:
        source_path = doc.metadata.get("source", "unknown")
        
        # Find the FAISS distance score for this document
        # Match by document content since reranking may have changed order
        similarity_score = None
        for original_doc, score in docs_with_scores:
            if original_doc.page_content == doc.page_content:
                similarity_score = score
                break
        
        # Fallback if not found (shouldn't happen)
        if similarity_score is None:
            similarity_score = 2.0
        
        # Calculate confidence based on FAISS L2 distance
        # Distance formula: sqrt(sum((v1[i] - v2[i])^2))
        if similarity_score < 0.8:
            confidence = "High"
            confidence_emoji = "🟢"
        elif similarity_score < 1.5:
            confidence = "Medium"
            confidence_emoji = "🟡"
        else:
            confidence = "Low"
            confidence_emoji = "🔴"
        
        sources.append({
            "source": source_path,
            "filename": os.path.basename(source_path),
            "content": doc.page_content,
            "similarity_score": round(similarity_score, 3),  # Round for readability
            "confidence": confidence,
            "confidence_emoji": confidence_emoji
        })
    
    # Construct the prompt with explicit ADR citation requirement
    priority_adrs_clause = ""
    if config.PRIORITY_ADRS:
        adrs_list = ", ".join(config.PRIORITY_ADRS)
        priority_adrs_clause = f" If the retrieved context contains a priority ADR ({adrs_list}), you MUST explicitly state 'Based on [ADR-XXX]...' at the beginning of your answer before providing the details."
    
    prompt = (
        f"System: You are a {config.ORG_NAME} AI Architect. "
        f"Using ONLY the following context: {context}, answer this question: {question}. "
        f"IMPORTANT:{priority_adrs_clause} "
        "If the answer is not in the context, say you do not know."
    )
    
    # Invoke the LLM using the configured provider
    answer = invoke_llm(prompt)
    
    # Clean the response: remove reasoning blocks and instruction echoes
    if isinstance(answer, str):
        # Save original for fallback
        original_answer = answer
        
        # Remove reasoning markers and blocks
        reasoning_markers = [
            "<thinking>",
            "<reasoning>",
            "</thinking>",
            "</reasoning>",
            "</think>",
            "<think>",
            "</think>",
            "<think>"
        ]
        
        # Check if there's a reasoning end marker - everything after it is the answer
        reasoning_end_markers = ["</think>", "</thinking>", "</think>"]
        for marker in reasoning_end_markers:
            if marker.lower() in answer.lower():
                # Split by reasoning end marker (case-insensitive) and take the last part
                import re
                pattern = re.compile(re.escape(marker), re.IGNORECASE)
                parts = pattern.split(answer)
                if len(parts) > 1:
                    answer = parts[-1].strip()
                    break
        
        # Remove reasoning markers
        for marker in reasoning_markers:
            answer = answer.replace(marker, "")
        
        # Split into lines for processing
        lines = answer.splitlines()
        filtered_lines = []
        in_reasoning_block = False
        
        # Common reasoning starters
        reasoning_starters = [
            "okay, let's see",
            "wait,",
            "the user is asking",
            "let me think",
            "looking at",
            "first,",
            "so,",
            "but wait",
            "however,",
            "the context",
            "according to the instructions"
        ]
        
        # Common answer starters (actual content)
        answer_starters = [
            "i do not know",
            "according to",
            "the requirements",
            "the decision",
            "based on",
            "the architecture",
            "the policy",
            "yes,",
            "no,",
            "each service",
            "all data",
            "encryption",
            "aws",
            "the following",
            "the decision records",
            "adr-",
            "decision records",
            "here are",
            "here is",
            "the list",
            "1.",
            "2.",
            "3.",
            "4.",
            "- adr",
            "* adr"
        ]
        
        # Track if we've found actual answer content
        found_answer_content = False
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                # Keep empty lines if we've found answer content (for formatting)
                if found_answer_content:
                    filtered_lines.append("")
                continue
            
            line_lower = line_stripped.lower()
            
            # Skip instruction echoes
            if "do not make up an answer" in line_lower:
                continue
            if "do not mention the context in your answer" in line_lower:
                continue
            
            # Check if this looks like a decision record (ADR format)
            is_adr_line = (
                "adr-" in line_lower or 
                line_stripped.startswith(("ADR-", "adr-")) or
                line_stripped.startswith(("- ADR", "* ADR", "1.", "2.", "3.", "4.", "5."))
            )
            
            # Check if this line starts reasoning
            is_reasoning = any(starter in line_lower for starter in reasoning_starters)
            
            # Check if this looks like an actual answer
            is_answer = any(starter in line_lower for starter in answer_starters) or is_adr_line
            
            if is_answer:
                in_reasoning_block = False
                found_answer_content = True
                filtered_lines.append(line)
            elif is_reasoning and not is_answer:
                # Only skip if it's clearly reasoning and not answer content
                if not found_answer_content:
                    in_reasoning_block = True
                    continue
                else:
                    # If we've already found answer content, keep it
                    filtered_lines.append(line)
            elif not in_reasoning_block or found_answer_content:
                # Include if not in reasoning block, or if we've found answer content
                filtered_lines.append(line)
        
        answer = "\n".join(filtered_lines).strip()
        
        # If we removed everything, try to find the actual answer in the original
        if not answer or len(answer) < 10:
            original_lines = original_answer.splitlines()
            # Look for lines that contain ADR references or look like answers
            potential_answers = []
            for line in original_lines:
                line_stripped = line.strip()
                if not line_stripped:
                    continue
                line_lower = line_stripped.lower()
                
                # Skip clear reasoning
                if any(starter in line_lower for starter in reasoning_starters):
                    continue
                
                # Keep lines that look like answers
                if (any(starter in line_lower for starter in answer_starters) or
                    "adr-" in line_lower or
                    line_stripped.startswith(("ADR-", "adr-", "-", "*", "1.", "2.", "3.", "4.", "5."))):
                    potential_answers.append(line_stripped)
            
            if potential_answers:
                answer = "\n".join(potential_answers).strip()
            elif original_answer.strip():
                # Last resort: return original if it's not empty
                # But try to remove obvious reasoning markers first
                fallback = original_answer
                for marker in reasoning_markers:
                    fallback = fallback.replace(marker, "")
                # Take last few lines that aren't reasoning
                fallback_lines = fallback.splitlines()
                last_lines = []
                for line in reversed(fallback_lines[-10:]):  # Check last 10 lines
                    line_stripped = line.strip()
                    if line_stripped and len(line_stripped) > 5:
                        line_lower = line_stripped.lower()
                        if not any(starter in line_lower for starter in reasoning_starters):
                            last_lines.insert(0, line_stripped)
                            if len(last_lines) >= 5:  # Get up to 5 lines
                                break
                if last_lines:
                    answer = "\n".join(last_lines).strip()
    
    # Ensure we never return an empty answer
    if not answer or len(answer.strip()) == 0:
        answer = "I do not know. The question is not covered in the available architecture documents."
    
    # Return the response and the sources
    return answer, sources

if __name__ == "__main__":
    # Example usage
    question = "What are the foundational principles for microservices architecture?"
    
    print("=" * 60)
    print("AI Architecture Auditor")
    print("=" * 60)
    print(f"\nQuestion: {question}\n")
    
    try:
        response, sources = ask_auditor(question)
        print("\n" + "=" * 60)
        print("Response:")
        print("=" * 60)
        print(response)
        print("\nSources:")
        for src in sources:
            print(f"- {src.get('filename', 'unknown')}")
    except Exception as e:
        print(f"\nError: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

import boto3
import json
import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

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
    
    # Initialize embeddings using the same model used during ingestion
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )
    
    # Load the FAISS index
    _vectorstore = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
    
    return _vectorstore

def invoke_deepseek_r1(prompt, region_name=None, max_tokens=1024, temperature=0.7, top_p=0.9):
    """
    Invoke DeepSeek-R1 model on AWS Bedrock.
    
    Args:
        prompt (str): The prompt to send to DeepSeek-R1
        region_name (str, optional): AWS region name. Defaults to us-east-1 or from env
        max_tokens (int, optional): Maximum tokens to generate. Defaults to 1024
        temperature (float, optional): Sampling temperature. Defaults to 0.7
        top_p (float, optional): Nucleus sampling parameter. Defaults to 0.9
        
    Returns:
        str: The response from DeepSeek-R1
    """
    # Get region from environment variable or use default
    if region_name is None:
        region_name = os.getenv('AWS_REGION', 'us-east-1')
    
    # Get credentials from environment (loaded from .env file)
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    
    # Create a Bedrock runtime client
    client_kwargs = {'region_name': region_name}
    if aws_access_key and aws_secret_key:
        client_kwargs['aws_access_key_id'] = aws_access_key
        client_kwargs['aws_secret_access_key'] = aws_secret_key
    
    bedrock_runtime = boto3.client('bedrock-runtime', **client_kwargs)
    
    # Model ID for DeepSeek-R1
    model_id = 'us.deepseek.r1-v1:0'
    
    # Prepare the request body for DeepSeek-R1
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
    
    # Extract the text content from the response
    if 'choices' in response_body and len(response_body['choices']) > 0:
        return response_body['choices'][0]['text']
    else:
        return "No response content found"

def ask_auditor(question):
    """
    Ask a question to the AI architect auditor using the FAISS index and DeepSeek-R1.
    
    Args:
        question (str): The question to ask
    
    Returns:
        tuple[str, list[dict]]: The response from DeepSeek-R1, and a list of sources with
        filename and content for each retrieved chunk.
    """
    # Load FAISS index if not already loaded
    vectorstore = load_faiss_index()
    
    # Search the FAISS index for relevant architecture context
    # Use k=10 to get more comprehensive results, especially for listing questions
    k = 10 if any(word in question.lower() for word in ["list", "all", "show", "enumerate"]) else 3
    relevant_docs = vectorstore.similarity_search(question, k=k)
    
    # Prepare context and source metadata
    context = "\n\n".join([doc.page_content for doc in relevant_docs])
    sources = []
    for doc in relevant_docs:
        source_path = doc.metadata.get("source", "unknown")
        sources.append({
            "source": source_path,
            "filename": os.path.basename(source_path),
            "content": doc.page_content
        })
    
    # Construct the prompt as specified
    prompt = (
        "System: You are a Digital Bank AI Architect. "
        f"Using ONLY the following context: {context}, answer this question: {question}. "
        "If the answer is not in the context, say you do not know."
    )
    
    # Invoke DeepSeek-R1 on AWS Bedrock using the boto3 runtime
    answer = invoke_deepseek_r1(prompt)
    
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

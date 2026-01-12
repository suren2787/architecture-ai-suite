"""
Solution Design Audit Module

This module provides functionality to audit solution designs against
architecture standards and ADRs stored in the FAISS knowledge base.
"""

import os
from brain import load_faiss_index, invoke_llm
import config


def discover_audit_aspects_from_standards():
    """
    Auto-discover audit aspects from enterprise standards documents.
    Uses LLM to extract key compliance areas from the knowledge base.
    
    Returns:
        list: List of discovered audit aspects
    """
    try:
        # Load FAISS index
        vectorstore = load_faiss_index()
        
        # Search for standards and compliance-related documents
        query = "enterprise architecture standards compliance requirements governance policies"
        standards_docs = vectorstore.similarity_search(query, k=10)
        
        if not standards_docs:
            return []
        
        # Combine standards content
        standards_text = "\n\n".join([doc.page_content for doc in standards_docs[:5]])
        
        # Ask LLM to extract key audit aspects
        prompt = f"""Analyze the following enterprise architecture standards and extract key compliance areas that should be audited in solution designs.

STANDARDS DOCUMENTS:
{standards_text}

Extract and return ONLY a comma-separated list of specific audit aspects/categories (maximum 15 items).
Focus on concrete, actionable areas like "Data Storage", "Authentication", "API Security", etc.

DO NOT include explanations or numbering. Output format: aspect1,aspect2,aspect3

Audit aspects:"""
        
        response = invoke_llm(prompt, max_tokens=256, temperature=0.3)
        
        # Parse the response
        if response:
            aspects = [aspect.strip() for aspect in response.split(',') if aspect.strip()]
            # Clean up any extra formatting
            aspects = [a.replace('\n', '').strip('- ').strip() for a in aspects]
            return [a for a in aspects if a and len(a) > 2][:15]  # Max 15 aspects
        
        return []
        
    except Exception as e:
        print(f"Warning: Could not auto-discover audit aspects: {e}")
        return []


def get_hybrid_audit_aspects():
    """
    Get audit aspects using hybrid approach:
    1. Start with configured aspects from config.env
    2. Add auto-discovered aspects from standards documents
    3. Deduplicate and return combined list
    
    Returns:
        list: Combined list of audit aspects
    """
    # Get manually configured aspects
    configured_aspects = config.AUDIT_ASPECTS
    
    # Get auto-discovered aspects
    discovered_aspects = discover_audit_aspects_from_standards()
    
    # Combine and deduplicate (case-insensitive)
    all_aspects = []
    seen_lower = set()
    
    # Add configured first (higher priority)
    for aspect in configured_aspects:
        aspect_lower = aspect.lower()
        if aspect_lower not in seen_lower:
            all_aspects.append(aspect)
            seen_lower.add(aspect_lower)
    
    # Add discovered aspects
    for aspect in discovered_aspects:
        aspect_lower = aspect.lower()
        if aspect_lower not in seen_lower:
            all_aspects.append(aspect)
            seen_lower.add(aspect_lower)
    
    return all_aspects if all_aspects else ["Architecture Compliance", "Security", "Data Management"]


def run_audit(design_text):
    """
    Audit a solution design against architecture standards and ADRs.
    
    Args:
        design_text (str): The solution design document text to audit
    
    Returns:
        str: Markdown table with audit results (Feature, Compliance, Required Action)
    """
    # Load FAISS index if not already loaded
    vectorstore = load_faiss_index()
    
    # Retrieve relevant standards and ADRs from FAISS
    # Use higher k value to get comprehensive coverage of standards
    k = 15
    relevant_docs = vectorstore.similarity_search(design_text, k=k)
    
    # Filter to prioritize configured priority ADRs
    priority_adrs = []
    other_standards = []
    
    priority_adr_list = config.PRIORITY_ADRS
    
    for doc in relevant_docs:
        content = doc.page_content
        source = doc.metadata.get("source", "")
        
        # Check if document matches any priority ADR
        is_priority = False
        for adr in priority_adr_list:
            if adr in content or adr in source:
                is_priority = True
                break
        
        if is_priority:
            priority_adrs.append(doc)
        else:
            other_standards.append(doc)
    
    # Combine priority ADRs first, then other relevant standards
    combined_docs = priority_adrs + other_standards[:10]  # Limit total context
    
    # Prepare standards context
    standards_context = "\n\n".join([doc.page_content for doc in combined_docs])
    
    # Get audit aspects using hybrid approach (configured + auto-discovered)
    audit_aspects = get_hybrid_audit_aspects()
    
    # Construct the audit prompt
    priority_adrs_text = ", ".join(config.PRIORITY_ADRS) if config.PRIORITY_ADRS else "key ADRs"
    audit_aspects_text = ", ".join(audit_aspects)  # Use hybrid aspects
    custom_instructions = f"\n{config.AUDIT_CUSTOM_INSTRUCTIONS}" if config.AUDIT_CUSTOM_INSTRUCTIONS else ""
    
    prompt = f"""You are a Lead Architecture Auditor for {config.ORG_NAME}.

Your task is to evaluate the following Solution Design against the Architecture Standards and ADRs provided below.

ARCHITECTURE STANDARDS AND ADRs:
{standards_context}

SOLUTION DESIGN TO AUDIT:
{design_text}

INSTRUCTIONS:
1. Carefully review the solution design against EVERY requirement in the standards
2. Pay special attention to {priority_adrs_text}
3. Identify ALL violations, gaps, and non-compliant features
4. For each issue found, provide specific required actions{custom_instructions}

OUTPUT FORMAT:
Return ONLY a Markdown table with the following columns:
- Feature: The specific feature or aspect being evaluated
- Compliance: "✅ Compliant", "⚠️ Partial", or "❌ Non-Compliant"
- Required Action: Specific action needed (or "None" if compliant)

IMPORTANT: 
- Include AT LEAST the following aspects in your audit: {audit_aspects_text}
- If a feature is not mentioned in the design, mark it as "⚠️ Partial" with action "Needs clarification in design"
- Output ONLY the table, no additional text before or after
- Do not include reasoning or thinking process in the output

Begin the table now:
"""
    
    # Invoke the LLM to perform the audit
    audit_result = invoke_llm(
        prompt,
        max_tokens=2048,  # Longer output for detailed audit
        temperature=0.3,  # Lower temperature for more focused analysis
        top_p=0.9
    )
    
    # Clean the response to ensure only the table is returned
    cleaned_result = _clean_audit_output(audit_result)
    
    return cleaned_result


def _clean_audit_output(raw_output):
    """
    Clean the LLM output to extract only the Markdown table.
    
    Args:
        raw_output (str): Raw output from the LLM
    
    Returns:
        str: Cleaned Markdown table
    """
    if not raw_output:
        return "| Feature | Compliance | Required Action |\n|---------|------------|------------------|\n| Error | ❌ Non-Compliant | Audit failed to generate results |"
    
    lines = raw_output.strip().split('\n')
    table_lines = []
    in_table = False
    
    for line in lines:
        stripped = line.strip()
        
        # Detect table start (header or separator)
        if '|' in stripped and ('Feature' in stripped or '---' in stripped):
            in_table = True
        
        # Collect table lines
        if in_table and '|' in stripped:
            table_lines.append(line)
        elif in_table and '|' not in stripped and stripped:
            # Table ended
            break
    
    # If we found a table, return it
    if table_lines:
        return '\n'.join(table_lines)
    
    # Fallback: try to find anything that looks like a table
    for i, line in enumerate(lines):
        if '|' in line and 'Feature' in line:
            # Found header, take from here
            remaining = lines[i:]
            table = []
            for tline in remaining:
                if '|' in tline:
                    table.append(tline)
                elif table:  # Stop when we hit non-table content
                    break
            if table:
                return '\n'.join(table)
    
    # Last resort: return the raw output if it contains table markers
    if '|' in raw_output:
        return raw_output.strip()
    
    # Failed to extract table
    return "| Feature | Compliance | Required Action |\n|---------|------------|------------------|\n| Error | ❌ Non-Compliant | No table found in audit output |"


if __name__ == "__main__":
    # Example usage
    sample_design = """
    # E-Commerce Platform Design
    
    ## Architecture Overview
    We will build an e-commerce platform with the following components:
    
    1. **User Authentication**: Using JWT tokens stored in browser localStorage
    2. **Data Storage**: Customer data will be stored in AWS RDS PostgreSQL in us-east-1
    3. **Payment Processing**: Integrate with Stripe API
    4. **Product Catalog**: Store product images in AWS S3
    5. **User Profile**: Store customer name, email, phone number, and purchase history
    
    ## Security
    - HTTPS for all communications
    - Password hashing with bcrypt
    
    ## Compliance
    - GDPR compliance for EU customers
    """
    
    print("=" * 80)
    print("Solution Design Audit")
    print("=" * 80)
    print("\nDesign Document:")
    print(sample_design)
    print("\n" + "=" * 80)
    print("Audit Results:")
    print("=" * 80)
    
    try:
        audit_table = run_audit(sample_design)
        print(audit_table)
    except Exception as e:
        print(f"\nError during audit: {e}")
        import traceback
        traceback.print_exc()

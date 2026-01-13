import streamlit as st
from brain import ask_auditor, load_faiss_index
from ingest import ingest_documents, ingest_from_confluence
from reviewer import run_audit
from confluence import fetch_page_content, validate_confluence_config
import confluence_sync
import config
import os

# Page configuration
st.set_page_config(
    page_title=f"{config.ORG_NAME}: Architecture AI Suite",
    page_icon=config.ORG_ICON,
    layout="wide"
)

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar
with st.sidebar:
    st.title(f"{config.ORG_ICON} {config.ORG_NAME}")
    st.markdown("---")
    
    # Display active model configuration
    provider = os.getenv('MODEL_PROVIDER', 'bedrock').upper()
    model_name = os.getenv('MODEL_NAME', 'us.deepseek.r1-v1:0')
    
    # Format model name for display
    if 'deepseek' in model_name.lower():
        display_name = "DeepSeek-R1"
    elif 'claude' in model_name.lower():
        display_name = "Claude"
    elif 'gpt-4' in model_name.lower():
        display_name = "GPT-4"
    elif 'gpt-3.5' in model_name.lower():
        display_name = "GPT-3.5"
    else:
        display_name = model_name.split('/')[-1] if '/' in model_name else model_name
    
    # Show proxy info for OpenWebUI
    if provider == 'OPENWEBUI':
        base_url = os.getenv('OPENWEBUI_BASE_URL', 'Not configured')
        st.markdown(f"**Provider:** {provider} (Proxy)")
        st.markdown(f"**Endpoint:** {base_url}")
        st.markdown(f"**Model:** {display_name}")
    else:
        st.markdown(f"**Provider:** {provider}")
        st.markdown(f"**Model:** {display_name}")
    st.markdown("---")
    
    # Confluence Sync section
    st.markdown("### 📂 Confluence Sync")
    
    # Show sync configuration
    sync_summary = confluence_sync.get_sync_summary()
    st.markdown(sync_summary)
    
    # Sync button
    if st.button("🔄 Sync from Confluence", use_container_width=True):
        # Check if Confluence is configured
        if not config.CONFLUENCE_SPACE_KEY:
            st.warning("⚠️ No Confluence space configured. Set CONFLUENCE_SPACE_KEY in config.env")
        else:
            with st.spinner("Syncing pages from Confluence..."):
                try:
                    success, message, num_pages = ingest_from_confluence()
                    
                    if success:
                        # Clear cached vectorstore to force reload
                        import brain
                        brain._vectorstore = None
                        
                        st.success(message)
                        st.info(f"📊 Synced {num_pages} page(s) into knowledge base")
                    else:
                        st.error(message)
                        
                except Exception as e:
                    st.error(f"❌ Sync failed: {str(e)}")
    
    st.markdown("---")
    
    # Refresh Knowledge Base button
    if st.button("🔄 Refresh Knowledge Base", use_container_width=True):
        with st.spinner("Re-scanning documents and updating FAISS index..."):
            try:
                # Run the ingestion process
                ingest_documents()
                
                # Clear the cached vectorstore to force reload
                import brain
                brain._vectorstore = None
                
                st.success("✅ Knowledge base updated successfully!")
                st.info("The FAISS index has been refreshed with the latest documents.")
            except Exception as e:
                st.error(f"❌ Error updating knowledge base: {str(e)}")
    
    st.markdown("---")
    
    # Clear history button
    if st.button("🗑️ Clear History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Main title
st.title(f"{config.ORG_ICON} {config.ORG_NAME}: Architecture AI Suite")
st.markdown("Intelligent tools for architecture governance and compliance")

# Create tabs for different modes
tab1, tab2 = st.tabs(["📚 Knowledge Bot", "🔍 Solution Auditor"])

# ===================================================================
# TAB 1: KNOWLEDGE BOT
# ===================================================================
with tab1:
    st.markdown("### Ask questions about architecture standards, security policies, and design decisions")
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask a question about architecture documents..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get response from auditor
        with st.chat_message("assistant"):
            with st.spinner("Searching architecture documents and generating response..."):
                try:
                    answer, sources = ask_auditor(prompt)
                    st.markdown(answer)
                    
                    # Enhanced Evidence section with confidence scores
                    if sources:
                        st.markdown("---")
                        st.markdown("### 📊 Evidence")
                        
                        for idx, src in enumerate(sources, 1):
                            filename = src.get("filename", "unknown")
                            content = src.get("content", "")
                            confidence = src.get("confidence", "Unknown")
                            similarity_score = src.get("similarity_score", 0.0)
                            
                            # Create expander with filename and confidence badge
                            confidence_emoji = src.get("confidence_emoji", "⚪")
                            
                            with st.expander(f"{confidence_emoji} **Source {idx}: {filename}** | Confidence: {confidence}"):
                                st.markdown(f"**Filename:** {filename}")
                                st.markdown(f"**Confidence Score:** {confidence} _(FAISS distance: {similarity_score:.3f})_")
                                st.markdown("**Relevant Content:**")
                                st.markdown(f"> _{content}_")
                    else:
                        st.info("No sources retrieved.")
                    
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                except Exception as e:
                    error_message = f"❌ Error: {str(e)}"
                    st.error(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": error_message})

# ===================================================================
# TAB 2: SOLUTION AUDITOR
# ===================================================================
with tab2:
    st.markdown("### Submit a solution design for compliance audit")
    priority_adrs_text = f" (especially {', '.join(config.PRIORITY_ADRS)})" if config.PRIORITY_ADRS else ""
    st.markdown(f"The auditor will evaluate your design against architecture standards and ADRs{priority_adrs_text}")
    
    # Input method selection
    input_method = st.radio(
        "Choose input method:",
        ["📝 Paste Text", "🔗 Confluence URL"],
        horizontal=True
    )
    
    design_input = None
    page_title = None
    
    if input_method == "📝 Paste Text":
        # Text area for solution design input
        design_input = st.text_area(
            "Paste your Solution Design document here:",
            height=300,
            placeholder="""Example:
# My E-Commerce Platform

## Architecture
- User authentication via JWT
- Data storage in AWS RDS (us-east-1)
- API Gateway for microservices

## Security
- HTTPS encryption
- Password hashing with bcrypt
...""",
            help="Provide your solution design document. Include architecture components, data storage, security measures, etc."
        )
    
    else:  # Confluence URL
        # Check if Confluence is configured
        is_configured, config_msg = validate_confluence_config()
        
        if not is_configured:
            st.warning(f"⚠️ {config_msg}")
            st.info("💡 To enable Confluence integration, add these to your `.env` file:\n```\nCONFLUENCE_EMAIL=your-email@company.com\nCONFLUENCE_API_TOKEN=your-api-token\n```")
        
        confluence_url = st.text_input(
            "Confluence Page URL:",
            placeholder="https://yourcompany.atlassian.net/wiki/spaces/ARCH/pages/123456/Design+Doc",
            help="Paste the full URL of your Confluence page containing the solution design"
        )
        
        if confluence_url and is_configured:
            with st.spinner("📥 Fetching content from Confluence..."):
                page_title, content, success = fetch_page_content(confluence_url)
                
                if success:
                    st.success(f"✅ Successfully fetched: **{page_title}**")
                    design_input = content
                    
                    # Show preview
                    with st.expander("📄 Preview fetched content"):
                        st.text(content[:1000] + "..." if len(content) > 1000 else content)
                else:
                    st.error(content)  # Error message
                    design_input = None
    
    # Audit button
    st.markdown("---")
    col1, col2 = st.columns([1, 4])
    with col1:
        run_audit_btn = st.button("🔍 Run Compliance Audit", type="primary", use_container_width=True)
    
    # Run audit when button is clicked
    if run_audit_btn:
        if not design_input or not design_input.strip():
            st.warning("⚠️ Please provide a solution design document before running the audit.")
        else:
            # Show what's being audited
            if page_title:
                st.info(f"🔍 Auditing Confluence page: **{page_title}**")
            
            with st.spinner("🔄 Analyzing design against architecture standards and ADRs..."):
                try:
                    # Call the audit function from reviewer.py
                    audit_result = run_audit(design_input)
                    
                    # Check if all items are compliant
                    compliant_count = audit_result.count("✅ Compliant")
                    non_compliant_count = audit_result.count("❌ Non-Compliant")
                    partial_count = audit_result.count("⚠️ Partial")
                    
                    # Display results
                    st.markdown("---")
                    st.markdown("### 📋 Compliance Audit Results")
                    
                    # Summary metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("✅ Compliant", compliant_count)
                    with col2:
                        st.metric("⚠️ Partial", partial_count)
                    with col3:
                        st.metric("❌ Non-Compliant", non_compliant_count)
                    
                    st.markdown("---")
                    
                    # Display the audit table
                    st.markdown(audit_result)
                    
                    # Success/failure message
                    st.markdown("---")
                    if non_compliant_count == 0 and partial_count == 0:
                        st.success("🎉 **Excellent!** Your design passes all ADRs and architecture standards. No violations found.")
                    elif non_compliant_count == 0:
                        st.info(f"✅ **Good!** No critical violations found. Please address {partial_count} partial compliance item(s) for full compliance.")
                    else:
                        st.error(f"❌ **Action Required:** {non_compliant_count} non-compliant item(s) found. Please review and address all violations before proceeding.")
                    
                except Exception as e:
                    st.error(f"❌ Error during audit: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())

# Footer
st.markdown("---")
st.markdown(
    f"<div style='text-align: center; color: #666; font-size: 0.9em; padding: 20px;'>"
    f"🔒 <strong>Internal Use Only</strong> | {config.ORG_NAME} Architecture Governance"
    "</div>",
    unsafe_allow_html=True
)

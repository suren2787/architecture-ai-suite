import streamlit as st
from brain import ask_auditor, load_faiss_index
from ingest import ingest_documents
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Digital Bank: Architecture AI Suite",
    page_icon="🏦",
    layout="wide"
)

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar
with st.sidebar:
    st.title("🏦 Digital Bank")
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
    
    st.markdown(f"**Provider:** {provider}")
    st.markdown(f"**Model:** {display_name}")
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
st.title("🏦 Digital Bank: Architecture AI Suite")
st.markdown("**Mode: Knowledge Bot** - Ask questions about architecture standards, security policies, and design decisions.")
st.info("💡 Coming Soon: Solution Design Audit | ADR Validator")

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
                        confidence_color = {
                            "High": "🟢",
                            "Medium": "🟡",
                            "Low": "🔴"
                        }.get(confidence, "⚪")
                        
                        with st.expander(f"{confidence_color} **Source {idx}: {filename}** | Confidence: {confidence}"):
                            st.markdown(f"**Filename:** {filename}")
                            st.markdown(f"**Confidence Score:** {confidence} _(similarity: {similarity_score:.3f})_")
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

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; font-size: 0.9em; padding: 20px;'>"
    "🔒 <strong>Internal Use Only</strong> | Digital Bank Architecture Governance"
    "</div>",
    unsafe_allow_html=True
)

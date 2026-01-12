import streamlit as st
from brain import ask_auditor

# Page configuration
st.set_page_config(
    page_title="Digital Bank: Architecture Knowledge Bot",
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
    st.markdown("**Model:** DeepSeek-R1 (AWS Bedrock)")
    st.markdown("---")
    
    # Clear history button
    if st.button("🗑️ Clear History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Main title
st.title("🏦 Digital Bank: Architecture Knowledge Bot")
st.markdown("Ask questions about architecture standards, security policies, and design decisions.")

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
                
                # Show sources in an expander
                with st.expander("Sources"):
                    if sources:
                        for src in sources:
                            filename = src.get("filename", "unknown")
                            content = src.get("content", "")
                            st.markdown(f"**{filename}**")
                            st.markdown(f"> {content}")
                            st.markdown("---")
                    else:
                        st.markdown("No sources retrieved.")
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                error_message = f"❌ Error: {str(e)}"
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})

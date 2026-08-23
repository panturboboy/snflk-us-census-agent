import streamlit as st
import os
from src.cortex_analyst import CortexAnalyst

# Page configuration
st.set_page_config(
    page_title="Census Demographics Chat",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styling
st.markdown("""
    <style>
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
        color: #0d47a1;
    }
    .assistant-message {
        background-color: #f5f5f5;
        color: #424242;
    }
    .data-table {
        margin-top: 1rem;
        font-size: 0.9rem;
    }
    </style>
    """, unsafe_allow_html=True)

# Load Streamlit secrets into environment (for Streamlit Cloud)
try:
    secrets_dict = st.secrets.to_dict()
    for key, value in secrets_dict.items():
        if not os.getenv(key):
            os.environ[key] = str(value)
except (FileNotFoundError, AttributeError, KeyError):
    # Secrets not configured (expected in local dev, use .env instead)
    pass

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "connection_initialized" not in st.session_state:
    st.session_state.connection_initialized = False
    try:
        # Test Snowflake connection
        from src.snowflake_client import SnowflakeClient
        from src.config import SnowflakeConfig

        SnowflakeConfig.validate()
        SnowflakeClient.get_connection()
        st.session_state.connection_initialized = True
    except ValueError as e:
        st.error(f"Configuration error: {e}")
        st.warning("Add these to Streamlit Cloud Secrets:\nSNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD, SNOWFLAKE_DATABASE, SNOWFLAKE_SCHEMA, SNOWFLAKE_WAREHOUSE, CORTEX_ANALYST_TOKEN")
        st.stop()
    except Exception as e:
        st.error(f"Snowflake connection error: {e}")
        st.info("Verify credentials are correct in Streamlit Cloud Secrets")
        st.stop()

# Header
st.title("📊 US Census Demographics Chat")
st.markdown("""
    Ask natural language questions about US population demographics.
    Powered by Snowflake Cortex Analyst and Census data.
""")

# Sidebar
with st.sidebar:
    st.header("About")
    st.markdown("""
    - **Data**: 2020 US Census (block group level)
    - **Dimensions**: State, County, Age Group, Sex
    - **Metrics**: Population, Margin of Error
    - **Powered by**: Snowflake Cortex Analyst
    """)

    if st.button("Clear Conversation", key="clear_button"):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.markdown("**Example Questions:**")
    examples = [
        "What is the population of California?",
        "Show population by age group nationally",
        "Compare population between Texas and New York",
        "What are the demographics of New York County?",
        "Population breakdown by sex for Florida"
    ]
    for i, example in enumerate(examples):
        # Create clickable button for each example
        if st.button(f"• {example}", key=f"example_{i}", use_container_width=True):
            # Update the input field with the clicked example
            st.session_state.user_input = example
            st.rerun()

# Main chat interface
if st.session_state.connection_initialized:
    # Display conversation history
    for message in st.session_state.messages:
        with st.container():
            if message["role"] == "user":
                st.markdown(f"""
                    <div class="chat-message user-message">
                    <strong>You:</strong> {message['content']}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="chat-message assistant-message">
                    <strong>Assistant:</strong> {message['content']}
                    </div>
                    """, unsafe_allow_html=True)

                # Display data table if available
                if "data" in message and message["data"]:
                    with st.expander("📊 View Data", expanded=False):
                        st.dataframe(
                            message["data"],
                            use_container_width=True,
                            key=f"data_{len(st.session_state.messages)}"
                        )

    # Input area with form (enables Enter key to submit)
    with st.form("chat_form", clear_on_submit=True):
        col1, col2 = st.columns([0.9, 0.1])

        with col1:
            user_input = st.text_input(
                "Ask about US Census demographics...",
                placeholder="e.g., What is the population of California?",
                key="user_input"
            )

        with col2:
            submit_button = st.form_submit_button("Send", use_container_width=True)

    # Process user input (Enter key or button click)
    if submit_button and user_input:
        # Add user message to history
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })

        # Show loading state
        with st.spinner("Analyzing your question..."):
            try:
                import threading
                import time

                result = None
                error = None

                def run_query():
                    nonlocal result, error
                    try:
                        # Query Cortex Analyst
                        result = CortexAnalyst.query(
                            user_input,
                            st.session_state.messages[:-1]  # Exclude current message for context
                        )
                    except Exception as e:
                        error = e

                # Run query in thread with timeout
                query_thread = threading.Thread(target=run_query, daemon=True)
                query_thread.start()
                query_thread.join(timeout=65)  # 65 second timeout

                if query_thread.is_alive():
                    # Query timed out
                    st.error("⏱️ Query timed out - Cortex Analyst not responding. Please try again.")
                    st.session_state.messages.pop()  # Remove the user message we added
                    st.rerun()
                    return

                if error:
                    raise error

                if result is None:
                    st.error("No response from Cortex Analyst")
                    st.session_state.messages.pop()  # Remove the user message we added
                    st.rerun()
                    return

                # Add assistant response to history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result['response'],
                    "data": result.get('data', []),
                    "success": result['success']
                })

                # Show error if query failed
                if not result['success']:
                    st.error(f"Query error: {result.get('error', 'Unknown error')}")

            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"I encountered an error: {str(e)}",
                    "success": False
                })

        # Rerun to display new message
        st.rerun()
else:
    st.error("Unable to connect to Snowflake. Please check your connection configuration.")

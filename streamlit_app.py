import streamlit as st
import os
import re
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
    .suggestion-button {
        margin-top: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

def extract_and_format_suggestions(response_text: str) -> tuple[str, list[str]]:
    """Extract suggested questions from response and return cleaned text + suggestions.

    Looks for patterns like:
    - "Try asking: ..."
    - "You could ask: ..."
    - "You can also ask: ..."

    Returns: (cleaned_response, list_of_suggestions)
    """
    suggestions = []

    # Pattern to match suggestion blocks
    patterns = [
        r"Try asking:?\s*\n\s*[-•]\s*(.+?)(?=\n|$)",  # "Try asking:" followed by bullets
        r"You (?:could|can) (?:also )?ask:?\s*\n\s*[-•]\s*(.+?)(?=\n|$)",  # "You can ask:" format
    ]

    for pattern in patterns:
        matches = re.finditer(pattern, response_text, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            suggestion = match.group(1).strip().rstrip('.?!')
            if suggestion and len(suggestion) > 5:  # Only add non-trivial suggestions
                suggestions.append(suggestion)

    # Remove suggestion sections from response text for cleaner display
    cleaned_text = response_text
    for pattern in patterns:
        cleaned_text = re.sub(pattern, "", cleaned_text, flags=re.IGNORECASE | re.MULTILINE)

    # Remove extra whitespace
    cleaned_text = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned_text).strip()

    return cleaned_text, list(dict.fromkeys(suggestions))  # Remove duplicates while preserving order

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

if "user_input_text" not in st.session_state:
    st.session_state.user_input_text = ""

if "submit_from_example" not in st.session_state:
    st.session_state.submit_from_example = False

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
            # Update the input field and flag for auto-submit
            st.session_state.user_input_text = example
            st.session_state.submit_from_example = True
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
                # Extract suggestions from response for clickable buttons
                response_text, suggestions = extract_and_format_suggestions(message['content'])

                st.markdown(f"""
                    <div class="chat-message assistant-message">
                    <strong>Assistant:</strong> {response_text}
                    </div>
                    """, unsafe_allow_html=True)

                # Display suggested questions as clickable buttons
                if suggestions:
                    st.markdown("**You can also try:**")
                    for i, suggestion in enumerate(suggestions):
                        if st.button(f"• {suggestion}", key=f"suggestion_{len(st.session_state.messages)}_{i}", use_container_width=True):
                            # Click suggestion: auto-populate input and submit
                            st.session_state.user_input_text = suggestion
                            st.session_state.submit_from_example = True
                            st.rerun()

                # Display data table if available
                if "data" in message and message["data"]:
                    with st.expander("📊 View Data", expanded=False):
                        st.dataframe(
                            message["data"],
                            use_container_width=True,
                            key=f"data_{len(st.session_state.messages)}"
                        )

    # Input area with form (enables Enter key)
    # CRITICAL: Do NOT use clear_on_submit=True - it breaks state tracking on 2nd submit
    st.divider()

    with st.form("chat_form"):
        col1, col2 = st.columns([0.9, 0.1])
        with col1:
            user_input = st.text_input(
                "Ask about US Census demographics...",
                placeholder="e.g., What is the population of California?",
                key="user_input_text"
            )
        with col2:
            send_clicked = st.form_submit_button("Send", use_container_width=True)

    # Process user input when Send button clicked, Enter pressed, or example auto-submitted
    should_submit = send_clicked or (st.session_state.submit_from_example and user_input)
    if should_submit and user_input:
        # Clear the auto-submit flag
        st.session_state.submit_from_example = False
        # Add user message to history
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })

        # Show loading state
        with st.spinner("Analyzing your question..."):
            try:
                # Query Cortex Analyst
                result = CortexAnalyst.query(
                    user_input,
                    st.session_state.messages[:-1]  # Exclude current message for context
                )

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

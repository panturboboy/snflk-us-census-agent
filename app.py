import streamlit as st
from src.config import SnowflakeConfig
from src.cortex_analyst import CortexAnalyst
from src.snowflake_client import SnowflakeClient

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
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "connection_initialized" not in st.session_state:
    st.session_state.connection_initialized = False
    try:
        SnowflakeConfig.validate()
        st.session_state.connection_initialized = True
    except Exception as e:
        st.error(f"Snowflake connection error: {e}")
        st.stop()

# Header
st.title("📊 US Census Demographics Chat")
st.markdown("Ask questions about US population demographics powered by Cortex Analyst.")

# Sidebar
with st.sidebar:
    st.header("About")
    st.markdown("""
    - **Data**: 2020 US Census
    - **Dimensions**: State, County, Age, Sex
    - **Powered by**: Snowflake Cortex Analyst
    """)

    if st.button("Clear Conversation"):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.markdown("**Example Questions:**")
    examples = [
        "What is the population of California?",
        "Show population by age group",
        "Compare Texas and New York",
        "Demographics of New York County?",
    ]
    for ex in examples:
        st.caption(f"• {ex}")

# Chat interface
if st.session_state.connection_initialized:
    # Display history
    for msg in st.session_state.messages:
        with st.container():
            if msg["role"] == "user":
                st.markdown(f"""
                    <div class="chat-message user-message">
                    <strong>You:</strong> {msg['content']}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="chat-message assistant-message">
                    <strong>Assistant:</strong> {msg['content']}
                    </div>
                    """, unsafe_allow_html=True)

                if "data" in msg and msg["data"]:
                    with st.expander("📊 View Data"):
                        st.dataframe(msg["data"], use_container_width=True)

    # Input
    col1, col2 = st.columns([0.9, 0.1])

    with col1:
        user_input = st.text_input("Ask about Census demographics...", key="user_input")

    with col2:
        submit_btn = st.button("Send")

    # Process input
    if submit_btn and user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.spinner("Analyzing..."):
            try:
                result = CortexAnalyst.query(user_input, st.session_state.messages[:-1])

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result['response'],
                    "data": result.get('data', []),
                    "success": result['success']
                })

                if not result['success']:
                    st.error(result.get('error'))

            except Exception as e:
                st.error(f"Error: {str(e)}")

        st.rerun()

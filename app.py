import os
import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# Load secret key from your local .env file
load_dotenv()

st.set_page_config(page_title="AI Chatbot", page_icon="🤖", layout="centered")

# Read key from laptop (.env) OR from Streamlit Cloud when hosted online
api_key = os.environ.get("OPENROUTER_API_KEY", "")
if not api_key:
    try:
        api_key = st.secrets["OPENROUTER_API_KEY"]
    except Exception:
        api_key = ""

with st.sidebar:
    st.title("⚙️ Settings")
    if api_key:
        st.success("✅ API Key loaded securely")
    else:
        api_key = st.text_input("OpenRouter API Key", type="password")

    model_name = st.selectbox(
        "Free Model",
        options=[
            "openrouter/free",
            "nvidia/nemotron-3.5-lightning:free",
            "nvidia/nemotron-3-ultra-550b-a55b:free",
        ],
    )

    system_prompt = st.text_area(
        "Assistant Role",
        value="You are a helpful, clear, and friendly AI assistant.",
        height=80,
    )

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

st.title("🤖 AI Chatbot")
st.caption("Built with Streamlit, LangChain & OpenRouter")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! Ask me anything to get started."}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Type your message here..."):
    if not api_key:
        st.warning("API key missing. Check your .env file or Streamlit Secrets.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    lc_messages = [SystemMessage(content=system_prompt)]
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            lc_messages.append(HumanMessage(content=msg["content"]))
        else:
            lc_messages.append(AIMessage(content=msg["content"]))

    llm = ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=0.7,
        streaming=True,
    )

    with st.chat_message("assistant"):
        try:
            def stream_response():
                for chunk in llm.stream(lc_messages):
                    if chunk.content:
                        yield chunk.content

            full_response = st.write_stream(stream_response())
            st.session_state.messages.append(
                {"role": "assistant", "content": full_response}
            )
        except Exception as e:
            st.error(f"Error: {e}")
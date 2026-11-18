import os
import re
import json
import uuid
import html
import httpx
from datetime import datetime
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# -----------------------------------------------------------------------------
# 1. BRANDING, PAGE CONFIGURATION & ENVIRONMENT SETUP
# -----------------------------------------------------------------------------
APP_NAME = "AETHER"
APP_TAGLINE = "Intelligence, Reimagined."

load_dotenv()

st.set_page_config(
    page_title=f"{APP_NAME} — {APP_TAGLINE}",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)


def render_html(raw_html: str):
    """Strip indentation and blank lines so Streamlit never treats HTML as a code block."""
    cleaned = "\n".join(
        line.strip() for line in raw_html.strip().splitlines() if line.strip()
    )
    st.markdown(cleaned, unsafe_allow_html=True)


def get_api_key() -> str:
    """Securely retrieve the OpenRouter API key from environment or Streamlit Secrets."""
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        try:
            key = str(st.secrets.get("OPENROUTER_API_KEY", "")).strip()
        except Exception:
            key = ""
    return key


def current_time_str() -> str:
    return datetime.now().strftime("%I:%M %p").lstrip("0")


def generate_chat_title(prompt: str) -> str:
    cleaned = re.sub(r"\s+", " ", prompt).strip()
    if len(cleaned) <= 36:
        return cleaned
    return cleaned[:35].rstrip() + "…"


# -----------------------------------------------------------------------------
# 2. MODELS, PERSONAS & CURATED PROMPTS
# -----------------------------------------------------------------------------
AVAILABLE_MODELS = {
    "openrouter/free": {
        "name": "Auto Router (Smart Free)",
        "badge": "AUTO • FREE",
        "desc": "Automatically routes to the fastest available free model.",
    },
    "nvidia/nemotron-3.5-lightning:free": {
        "name": "NVIDIA Nemotron 3.5 Lightning",
        "badge": "FAST • FREE",
        "desc": "Low-latency reasoning and crisp everyday responses.",
    },
    "nvidia/nemotron-3-ultra-550b-a55b:free": {
        "name": "NVIDIA Nemotron 3 Ultra 550B",
        "badge": "DEEP • FREE",
        "desc": "High-capacity model for complex coding and analysis.",
    },
}

PERSONA_PRESETS = {
    "Balanced Intelligence": (
        f"You are {APP_NAME}, an intelligent, articulate, and helpful AI assistant. "
        "Provide clear, well-structured, accurate answers using clean Markdown formatting."
    ),
    "Senior Code Architect": (
        f"You are {APP_NAME} in Code Architect mode. Write clean, production-grade, well-commented code. "
        "Explain time/space complexity, edge cases, and best practices clearly."
    ),
    "Academic Mentor": (
        f"You are {APP_NAME} in Academic Mentor mode. Break down complex concepts from first principles "
        "using intuitive analogies, structured sections, and concise summaries."
    ),
    "Creative Strategist": (
        f"You are {APP_NAME} in Creative Studio mode. Generate original, high-impact ideas, sharp copy, "
        "and structured frameworks with bold, imaginative thinking."
    ),
}

WELCOME_CARDS = [
    {
        "icon": "◈",
        "title": "Explain Something",
        "subtitle": "Understand complex topics with intuitive clarity",
        "prompt": "Explain how Large Language Models and attention mechanisms work in simple, intuitive terms with a real-world analogy.",
    },
    {
        "icon": "⌘",
        "title": "Code Assistant",
        "subtitle": "Write, debug, and optimize clean code",
        "prompt": "Write a clean, well-documented Python function with error handling and explain how to optimize its performance.",
    },
    {
        "icon": "✎",
        "title": "Smart Writer",
        "subtitle": "Draft, refine, and elevate written content",
        "prompt": "Help me structure and write a compelling executive summary for an innovative AI student project.",
    },
    {
        "icon": "✦",
        "title": "Creative Studio",
        "subtitle": "Brainstorm bold ideas and fresh perspectives",
        "prompt": "Brainstorm 5 creative, high-impact ways AI assistants can transform university learning and research.",
    },
]

APP_LOGO_SVG = (
    '<svg width="32" height="32" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">'
    '<defs>'
    '<linearGradient id="aetherGrad1" x1="2" y1="2" x2="34" y2="34" gradientUnits="userSpaceOnUse">'
    '<stop offset="0%" stop-color="#8B5CF6"/>'
    '<stop offset="100%" stop-color="#22D3EE"/>'
    '</linearGradient>'
    '<linearGradient id="aetherGrad2" x1="34" y1="4" x2="6" y2="32" gradientUnits="userSpaceOnUse">'
    '<stop offset="0%" stop-color="#22D3EE" stop-opacity="0.9"/>'
    '<stop offset="100%" stop-color="#8B5CF6" stop-opacity="0.25"/>'
    '</linearGradient>'
    '</defs>'
    '<rect x="2" y="2" width="32" height="32" rx="10" fill="url(#aetherGrad1)" fill-opacity="0.14" stroke="url(#aetherGrad1)" stroke-width="1.5"/>'
    '<polygon points="18,7 27,13.5 23.5,25.5 12.5,25.5 9,13.5" stroke="url(#aetherGrad1)" stroke-width="1.75" fill="url(#aetherGrad2)"/>'
    '<circle cx="18" cy="17" r="2.7" fill="#F5F5FA"/>'
    '</svg>'
)


# -----------------------------------------------------------------------------
# 3. SESSION STATE INITIALIZATION
# -----------------------------------------------------------------------------
def init_session_state():
    if "theme" not in st.session_state:
        st.session_state.theme = "dark"

    if "conversations" not in st.session_state:
        first_id = str(uuid.uuid4())[:8]
        st.session_state.conversations = {
            first_id: {
                "title": "New Conversation",
                "messages": [],
                "created_at": current_time_str(),
            }
        }
        st.session_state.active_chat_id = first_id

    if (
        "active_chat_id" not in st.session_state
        or st.session_state.active_chat_id not in st.session_state.conversations
    ):
        if st.session_state.conversations:
            st.session_state.active_chat_id = next(iter(st.session_state.conversations))
        else:
            new_id = str(uuid.uuid4())[:8]
            st.session_state.conversations[new_id] = {
                "title": "New Conversation",
                "messages": [],
                "created_at": current_time_str(),
            }
            st.session_state.active_chat_id = new_id

    if "selected_model" not in st.session_state:
        st.session_state.selected_model = "openrouter/free"

    if "selected_persona" not in st.session_state:
        st.session_state.selected_persona = "Balanced Intelligence"

    if "system_prompt" not in st.session_state:
        st.session_state.system_prompt = PERSONA_PRESETS["Balanced Intelligence"]

    if "pending_prompt" not in st.session_state:
        st.session_state.pending_prompt = None

    if "regenerate_requested" not in st.session_state:
        st.session_state.regenerate_requested = False

    if "confirm_clear" not in st.session_state:
        st.session_state.confirm_clear = False

    if "renaming_chat" not in st.session_state:
        st.session_state.renaming_chat = False

    if "manual_api_key" not in st.session_state:
        st.session_state.manual_api_key = ""


def create_new_chat():
    current = st.session_state.conversations.get(st.session_state.active_chat_id)
    if current and len(current["messages"]) == 0:
        st.session_state.confirm_clear = False
        st.session_state.renaming_chat = False
        return

    new_id = str(uuid.uuid4())[:8]
    st.session_state.conversations[new_id] = {
        "title": "New Conversation",
        "messages": [],
        "created_at": current_time_str(),
    }
    st.session_state.active_chat_id = new_id
    st.session_state.confirm_clear = False
    st.session_state.renaming_chat = False


def get_follow_up_suggestions(last_user_msg: str, last_ai_msg: str) -> list[str]:
    """Generate instant, context-aware follow-up prompts without extra API calls."""
    combined = (last_user_msg + " " + last_ai_msg).lower()
    if any(k in combined for k in ["```", "def ", "function", "python", "code", "bug", "error", "api"]):
        return [
            "Add edge-case handling and unit tests for this code",
            "Explain the time and space complexity step by step",
            "Show a cleaner or more optimized alternative",
        ]
    if any(k in combined for k in ["write", "draft", "essay", "email", "summary", "pitch"]):
        return [
            "Make it more concise and impactful",
            "Rewrite this in a more executive, persuasive tone",
            "Give me 3 alternative headline options",
        ]
    if any(k in combined for k in ["idea", "brainstorm", "strategy", "project", "design"]):
        return [
            "Pick the strongest option and build an action plan",
            "What are the biggest risks and how do we solve them?",
            "Give me 3 even more unconventional ideas",
        ]
    return [
        "Break this down with a concrete real-world example",
        "Summarize the 3 most important takeaways",
        "What should I explore next on this topic?",
    ]


# -----------------------------------------------------------------------------
# 4. DESIGN SYSTEM & CUSTOM CSS
# -----------------------------------------------------------------------------
def inject_design_system(theme: str):
    if theme == "dark":
        tokens = {
            "bg_main": "#09090F",
            "bg_sidebar": "#10111A",
            "bg_card": "#171824",
            "bg_elevated": "#1E2030",
            "bg_user_msg": "linear-gradient(135deg, rgba(139, 92, 246, 0.18), rgba(34, 211, 238, 0.08))",
            "border_user_msg": "rgba(139, 92, 246, 0.35)",
            "border_subtle": "rgba(255, 255, 255, 0.08)",
            "border_hover": "rgba(139, 92, 246, 0.45)",
            "text_primary": "#F5F5FA",
            "text_secondary": "#9293A5",
            "violet": "#8B5CF6",
            "cyan": "#22D3EE",
            "ambient_glow": (
                "radial-gradient(circle at 50% -10%, rgba(139, 92, 246, 0.16), transparent 52%), "
                "radial-gradient(circle at 82% 14%, rgba(34, 211, 238, 0.09), transparent 40%)"
            ),
            "grid_line": "rgba(255, 255, 255, 0.022)",
            "input_bg": "#141521",
            "code_bg": "#0D0E16",
        }
    else:
        tokens = {
            "bg_main": "#F8F9FC",
            "bg_sidebar": "#F1F3F9",
            "bg_card": "#FFFFFF",
            "bg_elevated": "#F4F6FB",
            "bg_user_msg": "linear-gradient(135deg, rgba(124, 58, 237, 0.11), rgba(8, 145, 178, 0.06))",
            "border_user_msg": "rgba(124, 58, 237, 0.30)",
            "border_subtle": "rgba(15, 23, 42, 0.09)",
            "border_hover": "rgba(124, 58, 237, 0.45)",
            "text_primary": "#0F172A",
            "text_secondary": "#64748B",
            "violet": "#7C3AED",
            "cyan": "#0891B2",
            "ambient_glow": (
                "radial-gradient(circle at 50% -10%, rgba(124, 58, 237, 0.09), transparent 52%), "
                "radial-gradient(circle at 82% 14%, rgba(8, 145, 178, 0.06), transparent 40%)"
            ),
            "grid_line": "rgba(15, 23, 42, 0.03)",
            "input_bg": "#FFFFFF",
            "code_bg": "#F1F5F9",
        }

    css = f"""
    <style>
    @import url('[https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap](https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap)');

    :root {{
        --bg-main: {tokens['bg_main']};
        --bg-sidebar: {tokens['bg_sidebar']};
        --bg-card: {tokens['bg_card']};
        --bg-elevated: {tokens['bg_elevated']};
        --bg-user-msg: {tokens['bg_user_msg']};
        --border-user-msg: {tokens['border_user_msg']};
        --border-subtle: {tokens['border_subtle']};
        --border-hover: {tokens['border_hover']};
        --text-primary: {tokens['text_primary']};
        --text-secondary: {tokens['text_secondary']};
        --violet: {tokens['violet']};
        --cyan: {tokens['cyan']};
        --input-bg: {tokens['input_bg']};
        --code-bg: {tokens['code_bg']};
    }}

    html, body, [data-testid="stAppViewContainer"] {{
        background-color: var(--bg-main) !important;
        background-image: {tokens['ambient_glow']} !important;
        color: var(--text-primary) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }}

    [data-testid="stAppViewContainer"]::before {{
        content: "";
        position: fixed;
        inset: 0;
        background-image:
            linear-gradient(to right, {tokens['grid_line']} 1px, transparent 1px),
            linear-gradient(to bottom, {tokens['grid_line']} 1px, transparent 1px);
        background-size: 44px 44px;
        mask-image: radial-gradient(ellipse at 50% 20%, black 25%, transparent 78%);
        pointer-events: none;
        z-index: 0;
    }}

    [data-testid="stHeader"] {{
        background: transparent !important;
    }}
    #MainMenu, footer, [data-testid="stDecoration"] {{
        visibility: hidden !important;
        height: 0 !important;
    }}

    .block-container {{
        max-width: 880px !important;
        padding-top: 1.15rem !important;
        padding-bottom: 6.5rem !important;
        position: relative;
        z-index: 1;
    }}

    [data-testid="stSidebar"] {{
        background-color: var(--bg-sidebar) !important;
        border-right: 1px solid var(--border-subtle) !important;
    }}
    [data-testid="stSidebar"] .block-container {{
        padding-top: 1.25rem !important;
        padding-bottom: 2rem !important;
    }}

    h1, h2, h3, h4, p, li, label, span, div {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}
    code, pre {{
        font-family: 'JetBrains Mono', monospace !important;
    }}

    .app-wordmark {{
        font-size: 1.12rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        color: var(--text-primary);
    }}
    .app-descriptor {{
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        padding: 0.2rem 0.55rem;
        border-radius: 999px;
        color: var(--cyan);
        background: rgba(34, 211, 238, 0.1);
        border: 1px solid rgba(34, 211, 238, 0.25);
    }}
    .app-model-pill {{
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        font-size: 0.78rem;
        font-weight: 500;
        color: var(--text-secondary);
        background: var(--bg-elevated);
        border: 1px solid var(--border-subtle);
        padding: 0.32rem 0.75rem;
        border-radius: 999px;
    }}
    .app-pulse-dot {{
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: #10B981;
        box-shadow: 0 0 8px #10B981;
        display: inline-block;
    }}

    .app-hero {{
        text-align: center;
        padding: 1.5rem 0.5rem 1.4rem 0.5rem;
        animation: fadeSlideUp 0.55s ease-out;
    }}
    .app-core-stage {{
        position: relative;
        width: 84px;
        height: 84px;
        margin: 0 auto 1.25rem auto;
        display: flex;
        align-items: center;
        justify-content: center;
    }}
    .app-core-orb {{
        width: 44px;
        height: 44px;
        border-radius: 50%;
        background: radial-gradient(circle at 32% 30%, #FFFFFF 0%, #22D3EE 35%, #8B5CF6 85%);
        box-shadow:
            0 0 28px rgba(139, 92, 246, 0.65),
            0 0 54px rgba(34, 211, 238, 0.35);
        animation: coreBreathe 3.6s ease-in-out infinite;
        z-index: 2;
    }}
    .app-core-ring-1 {{
        position: absolute;
        inset: 6px;
        border-radius: 50%;
        border: 1.5px solid rgba(139, 92, 246, 0.45);
        border-top-color: #22D3EE;
        animation: spinSlow 8s linear infinite;
    }}
    .app-core-ring-2 {{
        position: absolute;
        inset: 0px;
        border-radius: 50%;
        border: 1px dashed rgba(34, 211, 238, 0.32);
        animation: spinReverse 14s linear infinite;
    }}
    .app-hero-kicker {{
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: var(--cyan);
        margin-bottom: 0.55rem;
    }}
    .app-hero-title {{
        font-size: clamp(2rem, 4vw, 2.85rem);
        font-weight: 700;
        letter-spacing: -0.03em;
        line-height: 1.15;
        color: var(--text-primary);
        margin-bottom: 0.75rem;
    }}
    .app-gradient-text {{
        background: linear-gradient(120deg, #8B5CF6 10%, #22D3EE 90%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}
    .app-hero-subtitle {{
        max-width: 580px;
        margin: 0 auto;
        font-size: 1rem;
        line-height: 1.6;
        color: var(--text-secondary);
    }}

    div.stButton > button {{
        background-color: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 14px !important;
        padding: 0.65rem 1rem !important;
        font-weight: 500 !important;
        transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1) !important;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08) !important;
    }}
    div.stButton > button:hover {{
        border-color: var(--border-hover) !important;
        background-color: var(--bg-elevated) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(139, 92, 246, 0.18) !important;
    }}
    div.stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, #8B5CF6 0%, #6D28D9 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.16) !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 18px rgba(139, 92, 246, 0.35) !important;
    }}
    div.stButton > button[kind="primary"]:hover {{
        background: linear-gradient(135deg, #9333EA 0%, #7C3AED 100%) !important;
        box-shadow: 0 6px 24px rgba(139, 92, 246, 0.5) !important;
    }}

    .app-welcome-cards div.stButton > button {{
        text-align: left !important;
        justify-content: flex-start !important;
        align-items: flex-start !important;
        min-height: 92px !important;
        padding: 1rem 1.1rem !important;
        border-radius: 16px !important;
        background: var(--bg-card) !important;
        line-height: 1.45 !important;
        white-space: pre-wrap !important;
    }}
    .app-welcome-cards div.stButton > button:hover {{
        border-color: rgba(34, 211, 238, 0.5) !important;
        box-shadow: 0 10px 28px rgba(139, 92, 246, 0.2), 0 0 0 1px rgba(139, 92, 246, 0.25) !important;
    }}

    .app-user-row {{
        display: flex;
        justify-content: flex-end;
        margin: 1.1rem 0 0.85rem 0;
        animation: fadeSlideUp 0.28s ease-out;
    }}
    .app-user-bubble {{
        max-width: 78%;
        background: var(--bg-user-msg);
        border: 1px solid var(--border-user-msg);
        border-radius: 18px 18px 4px 18px;
        padding: 0.85rem 1.15rem;
        color: var(--text-primary);
        font-size: 0.96rem;
        line-height: 1.6;
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.12);
        word-wrap: break-word;
    }}
    .app-msg-meta {{
        font-size: 0.72rem;
        color: var(--text-secondary);
        margin-top: 0.35rem;
        display: flex;
        align-items: center;
        gap: 0.45rem;
    }}
    .app-ai-header {{
        display: flex;
        align-items: center;
        gap: 0.6rem;
        margin-top: 0.75rem;
        margin-bottom: 0.45rem;
    }}
    .app-ai-badge {{
        width: 26px;
        height: 26px;
        border-radius: 8px;
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.25), rgba(34, 211, 238, 0.2));
        border: 1px solid rgba(139, 92, 246, 0.45);
        display: inline-flex;
        align-items: center;
        justify-content: center;
        color: var(--cyan);
        font-size: 0.85rem;
        font-weight: 700;
    }}
    .app-ai-name {{
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--text-primary);
        letter-spacing: 0.03em;
    }}
    .app-ai-tag {{
        font-size: 0.72rem;
        color: var(--text-secondary);
        background: var(--bg-elevated);
        padding: 0.12rem 0.5rem;
        border-radius: 999px;
        border: 1px solid var(--border-subtle);
    }}

    [data-testid="stMarkdownContainer"] p {{
        font-size: 0.97rem;
        line-height: 1.68;
        color: var(--text-primary);
    }}
    [data-testid="stCode"] {{
        background-color: var(--code-bg) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 12px !important;
    }}

    .app-sidebar-section {{
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.11em;
        text-transform: uppercase;
        color: var(--text-secondary);
        margin: 1.15rem 0 0.5rem 0;
    }}
    .app-spec-card {{
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: 12px;
        padding: 0.7rem 0.85rem;
        margin-top: 0.45rem;
        margin-bottom: 0.65rem;
    }}
    .app-spec-row {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-size: 0.75rem;
        color: var(--text-secondary);
        margin-bottom: 0.25rem;
    }}
    .app-free-pill {{
        font-size: 0.68rem;
        font-weight: 600;
        color: #10B981;
        background: rgba(16, 185, 129, 0.12);
        border: 1px solid rgba(16, 185, 129, 0.28);
        padding: 0.1rem 0.45rem;
        border-radius: 999px;
    }}
    .app-status-card {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: 12px;
        padding: 0.65rem 0.85rem;
        font-size: 0.8rem;
    }}

    [data-testid="stBottom"], [data-testid="stBottom"] > div {{
        background: transparent !important;
    }}
    [data-testid="stChatInput"] {{
        max-width: 880px !important;
        margin: 0 auto !important;
        background: var(--input-bg) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 18px !important;
        box-shadow: 0 12px 36px rgba(0, 0, 0, 0.28) !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }}
    [data-testid="stChatInput"]:focus-within {{
        border-color: var(--violet) !important;
        box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.22), 0 12px 36px rgba(0, 0, 0, 0.32) !important;
    }}
    [data-testid="stChatInput"] textarea {{
        color: var(--text-primary) !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.96rem !important;
    }}

    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea,
    [data-baseweb="select"] > div {{
        background-color: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border-color: var(--border-subtle) !important;
        border-radius: 12px !important;
    }}

    @keyframes coreBreathe {{
        0%, 100% {{ transform: scale(0.95); box-shadow: 0 0 24px rgba(139, 92, 246, 0.6), 0 0 46px rgba(34, 211, 238, 0.3); }}
        50% {{ transform: scale(1.06); box-shadow: 0 0 36px rgba(139, 92, 246, 0.85), 0 0 68px rgba(34, 211, 238, 0.5); }}
    }}
    @keyframes spinSlow {{
        from {{ transform: rotate(0deg); }}
        to {{ transform: rotate(360deg); }}
    }}
    @keyframes spinReverse {{
        from {{ transform: rotate(360deg); }}
        to {{ transform: rotate(0deg); }}
    }}
    @keyframes fadeSlideUp {{
        from {{ opacity: 0; transform: translateY(8px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    </style>
    """
    render_html(css)


def render_copy_button(text_to_copy: str, theme: str, key_suffix: str):
    """Render a zero-rerun one-click clipboard copy button inside a compact transparent frame."""
    safe_json = json.dumps(text_to_copy)
    if theme == "dark":
        bg = "#171824"
        bg_hover = "#1E2030"
        border = "rgba(255,255,255,0.10)"
        color = "#9293A5"
        color_hover = "#F5F5FA"
    else:
        bg = "#FFFFFF"
        bg_hover = "#F4F6FB"
        border = "rgba(15,23,42,0.12)"
        color = "#64748B"
        color_hover = "#0F172A"

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
      body {{
        margin: 0;
        padding: 0;
        background: transparent;
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
      }}
      button {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: {bg};
        color: {color};
        border: 1px solid {border};
        border-radius: 10px;
        padding: 5px 11px;
        font-size: 12px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.18s ease;
      }}
      button:hover {{
        background: {bg_hover};
        color: {color_hover};
        border-color: rgba(139, 92, 246, 0.45);
      }}
    </style>
    </head>
    <body>
      <button id="btn_{key_suffix}" onclick="copyText()">📋 Copy</button>
      <script>
        const payload = {safe_json};
        function copyText() {{
          const btn = document.getElementById("btn_{key_suffix}");
          if (navigator.clipboard && window.isSecureContext) {{
            navigator.clipboard.writeText(payload).then(() => {{
              btn.innerText = "✓ Copied";
              btn.style.color = "#10B981";
              setTimeout(() => {{
                btn.innerText = "📋 Copy";
                btn.style.color = "{color}";
              }}, 1800);
            }});
          }} else {{
            const ta = document.createElement("textarea");
            ta.value = payload;
            document.body.appendChild(ta);
            ta.select();
            document.execCommand("copy");
            document.body.removeChild(ta);
            btn.innerText = "✓ Copied";
            btn.style.color = "#10B981";
            setTimeout(() => {{
              btn.innerText = "📋 Copy";
              btn.style.color = "{color}";
            }}, 1800);
          }}
        }}
      </script>
    </body>
    </html>
    """
    components.html(html_code, height=34)


# -----------------------------------------------------------------------------
# 5. INITIALIZE APP & INJECT STYLES
# -----------------------------------------------------------------------------
init_session_state()
inject_design_system(st.session_state.theme)

env_or_secret_key = get_api_key()
effective_api_key = env_or_secret_key if env_or_secret_key else st.session_state.manual_api_key

active_chat_id = st.session_state.active_chat_id
active_chat = st.session_state.conversations[active_chat_id]


# -----------------------------------------------------------------------------
# 6. SIDEBAR NAVIGATION & CONFIGURATION PANEL
# -----------------------------------------------------------------------------
with st.sidebar:
    render_html(
        f"""
        <div style="display:flex; align-items:center; gap:0.65rem; padding:0.2rem 0 0.85rem 0;">
            {APP_LOGO_SVG}
            <div>
                <div style="font-weight:700; font-size:1.08rem; letter-spacing:0.08em; line-height:1.1;">{APP_NAME}</div>
                <div style="font-size:0.72rem; color:var(--text-secondary);">{APP_TAGLINE}</div>
            </div>
        </div>
        """
    )

    if st.button("＋  New Chat", type="primary", use_container_width=True, key="sidebar_new_chat"):
        create_new_chat()
        st.rerun()

    render_html('<div class="app-sidebar-section">Conversations</div>')
    search_query = st.text_input(
        "Search chats",
        placeholder="🔍 Search conversations...",
        label_visibility="collapsed",
        key="chat_search_input",
    ).strip().lower()

    chat_ids = list(reversed(list(st.session_state.conversations.keys())))
    filtered_ids = [
        cid
        for cid in chat_ids
        if not search_query
        or search_query in st.session_state.conversations[cid]["title"].lower()
        or any(
            search_query in m["content"].lower()
            for m in st.session_state.conversations[cid]["messages"]
        )
    ]

    if not filtered_ids:
        st.caption("No matching conversations.")
    else:
        for cid in filtered_ids[:10]:
            chat_obj = st.session_state.conversations[cid]
            is_active = cid == active_chat_id
            prefix = "▸ " if is_active else "   "
            label = f"{prefix}{chat_obj['title']}"
            if st.button(
                label,
                key=f"select_chat_{cid}",
                use_container_width=True,
            ):
                st.session_state.active_chat_id = cid
                st.session_state.confirm_clear = False
                st.session_state.renaming_chat = False
                st.rerun()

    if active_chat["messages"]:
        c_ren, c_del = st.columns(2)
        with c_ren:
            if st.button("✏️ Rename", use_container_width=True, key="btn_toggle_rename"):
                st.session_state.renaming_chat = not st.session_state.renaming_chat
                st.rerun()
        with c_del:
            if st.button("🗑️ Delete", use_container_width=True, key="btn_delete_chat"):
                del st.session_state.conversations[active_chat_id]
                if not st.session_state.conversations:
                    new_id = str(uuid.uuid4())[:8]
                    st.session_state.conversations[new_id] = {
                        "title": "New Conversation",
                        "messages": [],
                        "created_at": current_time_str(),
                    }
                    st.session_state.active_chat_id = new_id
                else:
                    st.session_state.active_chat_id = list(st.session_state.conversations.keys())[-1]
                st.session_state.renaming_chat = False
                st.rerun()

        if st.session_state.renaming_chat:
            new_title = st.text_input(
                "Rename conversation",
                value=active_chat["title"],
                label_visibility="collapsed",
                key="rename_title_box",
            )
            if st.button("Save Title", use_container_width=True, key="save_title_btn"):
                if new_title.strip():
                    active_chat["title"] = new_title.strip()
                st.session_state.renaming_chat = False
                st.rerun()

    render_html('<div class="app-sidebar-section">AI Model</div>')
    model_keys = list(AVAILABLE_MODELS.keys())
    selected_model = st.selectbox(
        "Model",
        options=model_keys,
        index=model_keys.index(st.session_state.selected_model)
        if st.session_state.selected_model in model_keys
        else 0,
        format_func=lambda m: AVAILABLE_MODELS[m]["name"],
        label_visibility="collapsed",
    )
    st.session_state.selected_model = selected_model
    model_meta = AVAILABLE_MODELS[selected_model]

    render_html(
        f"""
        <div class="app-spec-card">
            <div class="app-spec-row">
                <span style="font-family:'JetBrains Mono',monospace; font-size:0.7rem;">{selected_model}</span>
                <span class="app-free-pill">{model_meta['badge']}</span>
            </div>
            <div style="font-size:0.74rem; color:var(--text-secondary); line-height:1.4;">
                {model_meta['desc']}
            </div>
        </div>
        """
    )

    render_html('<div class="app-sidebar-section">Assistant Personality</div>')
    with st.expander(f"🎭 {st.session_state.selected_persona}", expanded=False):
        preset_choice = st.selectbox(
            "Preset Mode",
            options=list(PERSONA_PRESETS.keys()),
            index=list(PERSONA_PRESETS.keys()).index(st.session_state.selected_persona),
        )
        if preset_choice != st.session_state.selected_persona:
            st.session_state.selected_persona = preset_choice
            st.session_state.system_prompt = PERSONA_PRESETS[preset_choice]
            st.rerun()

        custom_prompt = st.text_area(
            "System Instructions",
            value=st.session_state.system_prompt,
            height=95,
            help=f"Customize how {APP_NAME} thinks, formats, and responds.",
        )
        st.session_state.system_prompt = custom_prompt

    render_html('<div class="app-sidebar-section">Gateway Status</div>')
    if effective_api_key:
        render_html(
            """
            <div class="app-status-card">
                <span style="font-weight:500;">OpenRouter API</span>
                <span style="color:#10B981; font-weight:600; font-size:0.76rem;">● Connected</span>
            </div>
            """
        )
    else:
        render_html(
            """
            <div class="app-status-card">
                <span style="font-weight:500;">OpenRouter API</span>
                <span style="color:#F59E0B; font-weight:600; font-size:0.76rem;">● Key Needed</span>
            </div>
            """
        )
        st.session_state.manual_api_key = st.text_input(
            "Paste OpenRouter Key",
            type="password",
            placeholder="sk-or-v1-...",
            value=st.session_state.manual_api_key,
        )

    render_html('<div class="app-sidebar-section">Controls</div>')
    if not st.session_state.confirm_clear:
        if st.button("🧹 Clear Current Chat", use_container_width=True, key="btn_clear_prompt"):
            st.session_state.confirm_clear = True
            st.rerun()
    else:
        st.warning("Clear all messages in this chat?")
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("Yes, Clear", type="primary", use_container_width=True, key="btn_clear_yes"):
                active_chat["messages"] = []
                active_chat["title"] = "New Conversation"
                st.session_state.confirm_clear = False
                st.rerun()
        with col_no:
            if st.button("Cancel", use_container_width=True, key="btn_clear_no"):
                st.session_state.confirm_clear = False
                st.rerun()

    with st.expander(f"ℹ️ About {APP_NAME}", expanded=False):
        st.markdown(
            f"**{APP_NAME}** (*{APP_TAGLINE}*) is built with Python, Streamlit, "
            "LangChain, and OpenRouter—engineered for speed, clarity, and zero-key-leak security."
        )


# -----------------------------------------------------------------------------
# 7. TOP APPLICATION HEADER BAR
# -----------------------------------------------------------------------------
h_left, h_right = st.columns([6, 4])
with h_left:
    render_html(
        f"""
        <div style="display:flex; align-items:center; gap:0.75rem; padding:0.25rem 0;">
            {APP_LOGO_SVG}
            <span class="app-wordmark">{APP_NAME}</span>
            <span class="app-descriptor">AI Assistant</span>
            <span class="app-model-pill">
                <span class="app-pulse-dot"></span>
                {AVAILABLE_MODELS[st.session_state.selected_model]['name']}
            </span>
        </div>
        """
    )

with h_right:
    b1, b2 = st.columns(2)
    with b1:
        theme_label = "☀️ Light" if st.session_state.theme == "dark" else "🌙 Dark"
        if st.button(theme_label, use_container_width=True, key="top_theme_toggle"):
            st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
            st.rerun()
    with b2:
        if st.button("＋ New Chat", use_container_width=True, key="top_new_chat"):
            create_new_chat()
            st.rerun()

render_html("<hr style='border:none; border-top:1px solid var(--border-subtle); margin:0.45rem 0 1.15rem 0;'>")


# -----------------------------------------------------------------------------
# 8. WELCOME SCREEN OR ACTIVE CONVERSATION VIEW
# -----------------------------------------------------------------------------
messages = active_chat["messages"]

if len(messages) == 0 and not st.session_state.pending_prompt:
    render_html(
        f"""
        <div class="app-hero">
            <div class="app-core-stage">
                <div class="app-core-ring-2"></div>
                <div class="app-core-ring-1"></div>
                <div class="app-core-orb"></div>
            </div>
            <div class="app-hero-kicker">{APP_NAME.upper()} • {APP_TAGLINE.upper()}</div>
            <div class="app-hero-title">
                Your thoughts. <span class="app-gradient-text">Amplified.</span>
            </div>
            <p class="app-hero-subtitle">
                Think Beyond. Discover More. Meet {APP_NAME} — an intelligent companion built to help you
                explore ideas, solve problems, and think beyond limits.
            </p>
        </div>
        """
    )

    render_html('<div class="app-welcome-cards">')
    row1 = st.columns(2, gap="medium")
    row2 = st.columns(2, gap="medium")
    card_slots = [row1[0], row1[1], row2[0], row2[1]]

    for idx, card in enumerate(WELCOME_CARDS):
        with card_slots[idx]:
            card_label = f"{card['icon']}  {card['title']}\n{card['subtitle']}"
            if st.button(card_label, key=f"welcome_card_{idx}", use_container_width=True):
                st.session_state.pending_prompt = card["prompt"]
                st.rerun()
    render_html("</div>")

else:
    for idx, msg in enumerate(messages):
        if msg["role"] == "user":
            escaped_text = html.escape(msg["content"]).replace("\n", "<br>")
            ts = msg.get("timestamp", "")
            render_html(
                f"""
                <div class="app-user-row">
                    <div class="app-user-bubble">
                        <div>{escaped_text}</div>
                        <div class="app-msg-meta" style="justify-content:flex-end;">
                            <span>You</span> • <span>{ts}</span>
                        </div>
                    </div>
                </div>
                """
            )
        else:
            ts = msg.get("timestamp", "")
            model_used = msg.get("model", st.session_state.selected_model)
            render_html(
                f"""
                <div class="app-ai-header">
                    <span class="app-ai-badge">✦</span>
                    <span class="app-ai-name">{APP_NAME}</span>
                    <span class="app-ai-tag">{model_used}</span>
                    <span style="font-size:0.72rem; color:var(--text-secondary);">{ts}</span>
                </div>
                """
            )
            st.markdown(msg["content"])

            is_last_ai = idx == len(messages) - 1
            if is_last_ai:
                act_c1, act_c2, _ = st.columns([1.3, 1.6, 7.1])
                with act_c1:
                    render_copy_button(msg["content"], st.session_state.theme, f"msg_{idx}")
                with act_c2:
                    if st.button("↻ Regenerate", key=f"regen_{idx}", use_container_width=True):
                        if len(messages) >= 2 and messages[-2]["role"] == "user":
                            messages.pop()
                            st.session_state.regenerate_requested = True
                            st.rerun()
            else:
                act_c1, _ = st.columns([1.3, 8.7])
                with act_c1:
                    render_copy_button(msg["content"], st.session_state.theme, f"msg_{idx}")

    if (
        len(messages) >= 2
        and messages[-1]["role"] == "assistant"
        and not st.session_state.pending_prompt
        and not st.session_state.regenerate_requested
    ):
        suggestions = get_follow_up_suggestions(messages[-2]["content"], messages[-1]["content"])
        render_html(
            "<div style='font-size:0.75rem; color:var(--text-secondary); margin:0.85rem 0 0.4rem 0;'>"
            "Suggested follow-ups</div>"
        )
        f_cols = st.columns(3, gap="small")
        for f_idx, sug in enumerate(suggestions):
            with f_cols[f_idx]:
                if st.button(f"↳ {sug}", key=f"followup_{len(messages)}_{f_idx}", use_container_width=True):
                    st.session_state.pending_prompt = sug
                    st.rerun()


# -----------------------------------------------------------------------------
# 9. FLOATING CHAT COMPOSER & STREAMING GENERATION PIPELINE
# -----------------------------------------------------------------------------
user_typed_prompt = st.chat_input(f"Ask {APP_NAME} anything...")

prompt_to_run = None
is_regeneration = False

if st.session_state.regenerate_requested:
    st.session_state.regenerate_requested = False
    if messages and messages[-1]["role"] == "user":
        prompt_to_run = messages[-1]["content"]
        is_regeneration = True
elif st.session_state.pending_prompt:
    prompt_to_run = st.session_state.pending_prompt
    st.session_state.pending_prompt = None
elif user_typed_prompt and user_typed_prompt.strip():
    prompt_to_run = user_typed_prompt.strip()

if prompt_to_run:
    if not effective_api_key:
        st.error("OpenRouter API key is missing. Add it in Streamlit Secrets, `.env`, or the sidebar.")
        st.stop()

    if not is_regeneration:
        if len(messages) == 0:
            active_chat["title"] = generate_chat_title(prompt_to_run)

        ts_now = current_time_str()
        messages.append(
            {
                "role": "user",
                "content": prompt_to_run,
                "timestamp": ts_now,
            }
        )

        escaped_text = html.escape(prompt_to_run).replace("\n", "<br>")
        render_html(
            f"""
            <div class="app-user-row">
                <div class="app-user-bubble">
                    <div>{escaped_text}</div>
                    <div class="app-msg-meta" style="justify-content:flex-end;">
                        <span>You</span> • <span>{ts_now}</span>
                    </div>
                </div>
            </div>
            """
        )

    lc_messages = [SystemMessage(content=st.session_state.system_prompt)]
    for m in messages:
        if m["role"] == "user":
            lc_messages.append(HumanMessage(content=m["content"]))
        else:
            lc_messages.append(AIMessage(content=m["content"]))

    render_html(
        f"""
        <div class="app-ai-header">
            <span class="app-ai-badge">✦</span>
            <span class="app-ai-name">{APP_NAME}</span>
            <span class="app-ai-tag">{st.session_state.selected_model}</span>
            <span style="font-size:0.72rem; color:var(--cyan);">● Generating…</span>
        </div>
        """
    )
    try:
        with httpx.Client(timeout=45.0, follow_redirects=True) as http_client:
            llm = ChatOpenAI(
                model=st.session_state.selected_model,
                api_key=effective_api_key,
                base_url="https://openrouter.ai/api/v1",
                temperature=0.7,
                streaming=True,
                http_client=http_client,
                default_headers={
                    "HTTP-Referer": "https://myfreeaichatbot.streamlit.app",
                    "X-Title": APP_NAME,
                },
            )

            try:
                def token_stream():
                    for chunk in llm.stream(lc_messages):
                        if chunk.content:
                            yield chunk.content

                full_response = st.write_stream(token_stream())
            except Exception as stream_exc:
                # Fallback to standard non-streaming request if local firewall/ISP drops SSE streams
                if "connection" in str(stream_exc).lower() or "protocol" in str(stream_exc).lower():
                    ai_msg = llm.invoke(lc_messages)
                    full_response = ai_msg.content
                    st.markdown(full_response)
                else:
                    raise stream_exc

        if full_response and str(full_response).strip():
            messages.append(
                {
                    "role": "assistant",
                    "content": str(full_response),
                    "timestamp": current_time_str(),
                    "model": st.session_state.selected_model,
                }
            )
            st.rerun()
        else:
            st.warning("The selected free model returned an empty response. Click **Regenerate** or switch models in the sidebar.")

    except Exception as exc:
        err_str = str(exc)
        cause_str = str(exc.__cause__) if exc.__cause__ else ""
        full_err = f"{err_str} {cause_str}".lower()

        if "429" in full_err or "rate" in full_err:
            st.error(
                "**Rate Limit Reached:** This free model is temporarily busy. "
                "Switch to another model in the sidebar and try again."
            )
        elif "401" in full_err or "auth" in full_err:
            st.error("**Authentication Error:** Your OpenRouter API key was rejected. Verify it in `.env` or Streamlit Secrets.")
        elif "timeout" in full_err or "502" in full_err or "503" in full_err:
            st.error("**Model Timeout:** The upstream provider took too long to respond. Click **Regenerate** or pick another free model.")
        else:
            st.error(f"**Connection Error:** {err_str} {f'({cause_str})' if cause_str else ''}")
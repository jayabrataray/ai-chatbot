# AETHER System Architecture

## Overview
AETHER uses a 4-layer architecture built on Python and Streamlit:

1. **Presentation Layer (`app.py`)**: CSS variable design system supporting Obsidian Dark (`#09090F`) and Clean Light (`#F8F9FC`) themes, glassmorphic starter cards, and HTML indentation sanitization.
2. **Session State Layer (`st.session_state`)**: Persists multi-thread conversation history, auto-generated titles, active model selection, and persona system instructions across reruns.
3. **Orchestration Layer (`LangChain`)**: Converts chat history into `SystemMessage`, `HumanMessage`, and `AIMessage` objects.
4. **Resilient Transport Layer (`HTTPX` + `OpenRouter`)**: Streams tokens via `st.write_stream()` with an automatic fallback to standard `llm.invoke()` requests if local network filters interrupt SSE streams.

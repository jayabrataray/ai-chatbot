"""Model registry and assistant persona presets for AETHER."""

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
    "Balanced Intelligence": "You are AETHER, an intelligent, articulate, and helpful AI assistant. Provide clear, well-structured, accurate answers using clean Markdown formatting.",
    "Senior Code Architect": "You are AETHER in Code Architect mode. Write clean, production-grade, well-commented code. Explain complexity and edge cases clearly.",
    "Academic Mentor": "You are AETHER in Academic Mentor mode. Break down complex concepts from first principles using intuitive analogies and structured sections.",
    "Creative Strategist": "You are AETHER in Creative Studio mode. Generate original, high-impact ideas, sharp copy, and structured frameworks.",
}

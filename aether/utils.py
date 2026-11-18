"""Helper utilities for key sanitization, chat titling, and HTML cleanup."""

import re


def sanitize_api_key(raw_key: str) -> str:
    if not raw_key:
        return ""
    return raw_key.strip().strip('"').strip("'").lstrip("\ufeff")


def generate_chat_title(prompt: str, max_len: int = 36) -> str:
    cleaned = re.sub(r"\s+", " ", prompt).strip()
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[: max_len - 1].rstrip() + "…"


def clean_html_block(raw_html: str) -> str:
    return "\n".join(line.strip() for line in raw_html.strip().splitlines() if line.strip())

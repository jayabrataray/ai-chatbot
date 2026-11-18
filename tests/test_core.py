import unittest
from aether.config import AVAILABLE_MODELS, PERSONA_PRESETS
from aether.utils import sanitize_api_key, generate_chat_title, clean_html_block


class TestAetherCore(unittest.TestCase):
    def test_models_and_personas(self):
        self.assertIn("openrouter/free", AVAILABLE_MODELS)
        self.assertIn("Balanced Intelligence", PERSONA_PRESETS)

    def test_sanitize_api_key(self):
        self.assertEqual(sanitize_api_key('  "sk-or-v1-abc123"  '), "sk-or-v1-abc123")
        self.assertEqual(sanitize_api_key(""), "")

    def test_generate_chat_title(self):
        self.assertEqual(generate_chat_title("Short title"), "Short title")
        self.assertTrue(generate_chat_title("Explain how transformer self-attention works in detail").endswith("…"))

    def test_clean_html_block(self):
        indented = "    <div>\n        <span>AETHER</span>\n    </div>"
        self.assertEqual(clean_html_block(indented), "<div>\n<span>AETHER</span>\n</div>")


if __name__ == "__main__":
    unittest.main()

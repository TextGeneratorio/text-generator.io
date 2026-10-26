import os


SELLER_ID = "toset"
SELLER_SECRET = "toset"
STRIPE_TEST_KEY = "toset"
STRIPE_LIVE_KEY = "toset"
STRIPE_TEST_SECRET = "toset"
STRIPE_LIVE_SECRET = "toset"
session_secret = dict(secret_key="toset")
discord_token = "toset"
discord_client_secret = "toset"
discord_client_id = "toset"
TEXT_GENERATOR_SECRET = "toset"
CLAUDE_API_KEY = "toset"

# Unified model-router credentials. Environment variables take precedence so
# deployments never need to commit provider secrets in this module.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "toset")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", CLAUDE_API_KEY)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "toset")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "toset")
XAI_API_KEY = os.getenv("XAI_API_KEY", "toset")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "toset")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "toset")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY", "toset")
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "toset")
Z_API_KEY = os.getenv("Z_API_KEY", "toset")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "toset")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "toset")
FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY", "toset")
NOUS_API_KEY = os.getenv("NOUS_API_KEY", "toset")

import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    YARN_API_KEY = os.environ.get("YARN_API_KEY")
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
    YARN_BASE_URL = "https://api.yarngpt.ai/api/v1"
    MAX_CONTENT_LENGTH = 15 * 1024 * 1024  # audio uploads
    POLL_START, POLL_MAX, POLL_TIMEOUT = 1.0, 5.0, 120
    VOICE_OVERRIDES = {
        code: os.environ.get(f"VOICE_{code.upper()}") or None
        for code in ("en", "ig", "ha", "yo", "pcm")
    }

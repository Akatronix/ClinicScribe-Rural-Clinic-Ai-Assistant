"""The five supported languages and how each one is handled."""

LANGUAGES = {
    "en": {
        "label": "English",
        "prompt_name": "clear, simple English",
        "voice_hints": ["english", '"en"'],
    },
    "ig": {
        "label": "Igbo",
        "prompt_name": "clear, natural Igbo",
        "voice_hints": ["igbo", '"ig"'],
    },
    "ha": {
        "label": "Hausa",
        "prompt_name": "clear, natural Hausa",
        "voice_hints": ["hausa", '"ha"'],
    },
    "yo": {
        "label": "Yoruba",
        "prompt_name": "clear, natural Yoruba, with tone marks",
        "voice_hints": ["yoruba", '"yo"'],
    },
    "pcm": {
        "label": "Nigerian Pidgin",
        "prompt_name": "easy Nigerian Pidgin (Naija) that a market woman or farmer will understand",
        "voice_hints": ["pidgin", "pcm"],
    },
}


def is_supported(code):
    return code in LANGUAGES

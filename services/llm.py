"""Groq-backed clinic assistant, replying in the patient's language."""
import re

from groq import Groq

from .languages import LANGUAGES

SYSTEM_PROMPT = """You are a warm, patient health assistant for a rural clinic in Nigeria.
Reply ONLY in {lang}. Many patients cannot read well and will hear your reply as speech.

Rules:
- Use short sentences and everyday words. At most 4 sentences. Plain text only: no lists, no markdown, no emojis.
- You give general health information. You never diagnose and never prescribe drug doses.
- Ask at most one simple follow-up question at a time.
- If you hear any danger sign (trouble breathing, chest pain, heavy bleeding, fits, a very sick baby, \
pregnancy bleeding or severe headache, snake bite, unconsciousness, thoughts of self-harm), tell the \
person to go to the nearest clinic or hospital NOW or call emergency services, before anything else.
- Always advise seeing the clinic nurse or doctor for anything that does not clearly get better.
- Be kind. Never shame the person. If you are unsure, say so and refer them to the clinic."""


def clean_for_speech(text):
    text = re.sub(r"[*_#`>~]+", "", text)
    text = re.sub(r"\s*\n+\s*", " ", text)
    return text.strip()


class ClinicLLM:
    def __init__(self, api_key, model):
        self.client = Groq(api_key=api_key)
        self.model = model

    def reply(self, language, history, message):
        messages = [{"role": "system", "content": SYSTEM_PROMPT.format(lang=LANGUAGES[language]["prompt_name"])}]
        for turn in history[-8:]:
            if turn.get("role") in ("user", "assistant") and isinstance(turn.get("content"), str):
                messages.append({"role": turn["role"], "content": turn["content"][:1500]})
        messages.append({"role": "user", "content": message[:1500]})
        out = self.client.chat.completions.create(model=self.model, messages=messages, temperature=0.3)
        return clean_for_speech(out.choices[0].message.content or "")

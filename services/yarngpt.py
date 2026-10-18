"""YarnGPT speech-to-text and text-to-speech client."""
import io
import json
import time
import uuid

import requests


class YarnError(RuntimeError):
    pass


class YarnGPT:
    def __init__(self, api_key, base_url, poll_start=1.0, poll_max=5.0, poll_timeout=120):
        self.key = api_key
        self.base = base_url
        self.poll_start, self.poll_max, self.poll_timeout = poll_start, poll_max, poll_timeout
        self._voices = None

    def _headers(self, idempotent=False):
        h = {"Authorization": f"Bearer {self.key}"}
        if idempotent:
            h["Idempotency-Key"] = str(uuid.uuid4())
        return h

    @staticmethod
    def _check(resp, context):
        if resp.ok:
            return
        try:
            err = resp.json().get("error", {})
        except ValueError:
            err = {}
        msg = err.get("user_message") or err.get("message") or resp.text[:200]
        raise YarnError(f"{context} failed: {err.get('code', resp.status_code)} - {msg}")

    def _poll(self, url, context):
        delay, deadline = self.poll_start, time.time() + self.poll_timeout
        while time.time() < deadline:
            time.sleep(delay)
            delay = min(delay * 1.5, self.poll_max)
            r = requests.get(url, headers=self._headers(), timeout=30)
            self._check(r, f"{context} poll")
            body = r.json()
            if body.get("status") == "completed":
                return body
            if body.get("status") == "failed":
                raise YarnError(f"{context} failed: {body.get('user_message') or body.get('error_message')}")
        raise YarnError(f"{context} timed out")

    def transcribe(self, wav_bytes, filename="speech.wav"):
        files = {"file": (filename, io.BytesIO(wav_bytes), "audio/wav")}
        r = requests.post(f"{self.base}/asr", headers=self._headers(True), files=files, timeout=45)
        self._check(r, "Speech upload")
        body = self._poll(f"{self.base}/asr/{r.json().get('job_id')}", "Speech recognition")
        return (body.get("transcript") or "").strip()

    def voices(self):
        if self._voices is None:
            r = requests.get(f"{self.base}/voices", headers=self._headers(), timeout=30)
            self._check(r, "Voice list")
            body = r.json()
            if isinstance(body, dict):
                body = next((body[k] for k in ("voices", "data", "items", "results") if isinstance(body.get(k), list)), [])
            self._voices = body if isinstance(body, list) else []
        return self._voices

    @staticmethod
    def voice_id(v):
        if isinstance(v, str):
            return v
        return next((v[k] for k in ("id", "name", "voice", "voice_id") if v.get(k)), None)

    def pick_voice(self, hints, override=None):
        if override:
            return override
        voices = self.voices()
        if not voices:
            raise YarnError("YarnGPT returned no voices. Set VOICE_<LANG> in .env.")
        dicts = [v for v in voices if isinstance(v, dict)]
        match = [v for v in dicts if any(h in json.dumps(v).lower() for h in hints)]
        default = [v for v in dicts if v.get("default")]
        chosen = (match or default or voices)[0]
        vid = self.voice_id(chosen)
        if not vid:
            raise YarnError(f"Could not read a voice id from {chosen}")
        return vid

    def synthesize(self, text, voice, fmt="wav"):
        r = requests.post(
            f"{self.base}/tts",
            headers={**self._headers(True), "Content-Type": "application/json"},
            json={"text": text, "voice": voice, "output_format": fmt},
            timeout=45,
        )
        self._check(r, "Speech synthesis")
        job_id = r.json().get("job_id")
        if not job_id:
            raise YarnError("Speech synthesis returned no job id")
        body = self._poll(f"{self.base}/status/{job_id}", "Speech synthesis")
        url = body.get("audio_url")
        if not url:
            raise YarnError("Speech synthesis finished without audio")
        audio = requests.get(url, timeout=60)
        audio.raise_for_status()
        if len(audio.content) < 1000:
            raise YarnError("Synthesised audio was empty")
        return audio.content

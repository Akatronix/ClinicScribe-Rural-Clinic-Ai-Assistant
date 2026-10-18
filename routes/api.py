from flask import Blueprint, Response, current_app, jsonify, request

from services.languages import LANGUAGES, is_supported
from services.llm import clean_for_speech
from services.yarngpt import YarnError

bp = Blueprint("api", __name__, url_prefix="/api")


def _lang(data=None):
    code = (data or {}).get("language") or request.values.get("language") or "en"
    return code if is_supported(code) else "en"


@bp.errorhandler(Exception)
def handle_error(exc):
    current_app.logger.exception("API error")
    if isinstance(exc, YarnError):
        return jsonify(error=str(exc)), 502
    return jsonify(error="Something went wrong. Please try again."), 500


@bp.get("/languages")
def languages():
    return jsonify([{"code": c, "label": v["label"]} for c, v in LANGUAGES.items()])


@bp.post("/transcribe")
def transcribe():
    f = request.files.get("file")
    if not f:
        return jsonify(error="No audio received."), 400
    return jsonify(text=current_app.extensions["yarn"].transcribe(f.read()))


@bp.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify(error="Empty message."), 400
    reply = current_app.extensions["llm"].reply(_lang(data), data.get("history") or [], message)
    return jsonify(reply=reply)


@bp.post("/tts")
def tts():
    data = request.get_json(silent=True) or {}
    text = clean_for_speech(data.get("text") or "")
    if not text:
        return jsonify(error="Nothing to speak."), 400
    lang = _lang(data)
    yarn = current_app.extensions["yarn"]
    voice = yarn.pick_voice(LANGUAGES[lang]["voice_hints"], current_app.config["VOICE_OVERRIDES"].get(lang))
    return Response(yarn.synthesize(text, voice), mimetype="audio/wav", headers={"X-Voice": voice})

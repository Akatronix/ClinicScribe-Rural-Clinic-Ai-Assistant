import sys

import click
from flask import Flask, render_template

from config import Config
from routes.api import bp as api_bp
from services.llm import ClinicLLM
from services.yarngpt import YarnGPT


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    if not Config.YARN_API_KEY or not Config.GROQ_API_KEY:
        sys.exit("Missing YARN_API_KEY or GROQ_API_KEY. Copy .env.example to .env and fill them in.")

    app.extensions["yarn"] = YarnGPT(
        Config.YARN_API_KEY, Config.YARN_BASE_URL, Config.POLL_START, Config.POLL_MAX, Config.POLL_TIMEOUT
    )
    app.extensions["llm"] = ClinicLLM(Config.GROQ_API_KEY, Config.GROQ_MODEL)
    app.register_blueprint(api_bp)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.cli.command("list-voices")
    def list_voices():
        """Print the YarnGPT voice catalogue."""
        for v in app.extensions["yarn"].voices():
            click.echo(v)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)

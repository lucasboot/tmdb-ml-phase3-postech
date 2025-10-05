from flask import Flask
from .config import Config
from .db import init_db
from .routes.api import api_bp
from .routes.dashboard import dash_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    init_db(app)

    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(dash_bp)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


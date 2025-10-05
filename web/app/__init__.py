from flask import Flask
from .config import Config
from .db import init_db
from .routes.api import api_bp
from .routes.dashboard import dash_bp
from .version import discover_version


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config.setdefault("APP_VERSION", discover_version())

    init_db(app)

    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(dash_bp)

    @app.context_processor
    def inject_app_version():
        return {"app_version": app.config.get("APP_VERSION", "dev")}

    @app.get("/health")
    def health():
        return {"status": "ok", "version": app.config.get("APP_VERSION", "dev")}

    return app


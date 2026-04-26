from flask import Flask
from flask_cors import CORS

from app.config import Settings
from app.swagger import register_swagger
from repositories.db import Database
from repositories.profile_repository import ProfileRepository
from routes.ai_routes import ai_blueprint


def create_app() -> Flask:
    settings = Settings.from_env()
    db = Database(settings)

    profile_repository = ProfileRepository(db)
    profile_repository.ensure_table()

    app = Flask(__name__)
    CORS(
        app,
        resources={r"/*": {"origins": settings.cors_origins}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )
    app.config["SETTINGS"] = settings
    app.config["DB"] = db

    app.register_blueprint(ai_blueprint)
    register_swagger(app)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "service": "lottus-ai-api"}

    return app

import os

from flask import Flask
from flask_cors import CORS

from .extensions import db, jwt
from .routes import api


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI=os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg2://sensor_user:sensor_password@localhost:5432/sensor_dashboard",
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY", "change-me-in-production"),
        INGEST_API_KEY=os.getenv("INGEST_API_KEY", "dev-ingest-token"),
    )

    if test_config:
        app.config.update(test_config)

    CORS(app, resources={r"/api/*": {"origins": os.getenv("FRONTEND_ORIGIN", "*")}})
    db.init_app(app)
    jwt.init_app(app)
    app.register_blueprint(api, url_prefix="/api")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app

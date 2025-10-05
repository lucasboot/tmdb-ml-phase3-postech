import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TMDB_API_KEY = os.getenv("TMDB_API_KEY")
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
    POLL_INTERVAL_MS = int(os.getenv("POLL_INTERVAL_MS", "30000"))


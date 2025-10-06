import os
from celery import Celery
from datetime import datetime
from .config import Config
from .db import db
from .models import ModelPrediction
from .tmdb import initial_ingest_movies, update_movies_incremental, collect_movies_by_year_range
from .ml import train_and_store
from flask import Flask

redis_url = os.getenv("REDIS_URL")
celery = Celery(__name__, broker=redis_url, backend=redis_url)

celery.conf.update(
    broker_connection_retry_on_startup=True,
    broker_use_ssl={'ssl_cert_reqs': 'none'} if redis_url and redis_url.startswith('rediss://') else None,
    redis_backend_use_ssl={'ssl_cert_reqs': 'none'} if redis_url and redis_url.startswith('rediss://') else None,
    imports=('app.celery_app',),
)

# celery.conf.beat_schedule = {
#     "update-movies-every-5-minutes": {
#         "task": "app.celery_app.task_update_movies",
#         "schedule": 5.0 * 60.0,
#     },
#     "train-model-every-hour": {
#         "task": "app.celery_app.task_train",
#         "schedule": 60.0 * 60.0,
#     },
# }


def make_flask_app():
    from . import create_app
    return create_app()


@celery.task(name="app.celery_app.task_initial_ingest")
def task_initial_ingest(start_year=2010, end_year=None, min_votes=50, max_pages_per_year=50):
    app = make_flask_app()
    with app.app_context():
        res = initial_ingest_movies(
            start_year=start_year,
            end_year=end_year,
            min_votes=min_votes,
            max_pages_per_year=max_pages_per_year
        )
        return res


@celery.task(name="app.celery_app.task_update_movies")
def task_update_movies(min_votes=50, max_pages=5):
    app = make_flask_app()
    with app.app_context():
        res = update_movies_incremental(
            min_votes=min_votes,
            max_pages=max_pages
        )
        return res


@celery.task(name="app.celery_app.task_ingest")
def task_ingest():
    app = make_flask_app()
    with app.app_context():
        res = collect_movies_by_year_range()
        return res


@celery.task(name="app.celery_app.task_train")
def task_train():
    app = make_flask_app()
    with app.app_context():
        res = train_and_store()
        return res


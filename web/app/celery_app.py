import os
from celery import Celery
from datetime import datetime
from .config import Config
from .db import db
from .models import ModelPrediction
from .tmdb import collect_popular_pages
from .ml import train_and_store
from flask import Flask

celery = Celery(__name__, broker=os.getenv("REDIS_URL"), backend=os.getenv("REDIS_URL"))

celery.conf.beat_schedule = {
    "fetch-tmdb-every-2-min": {
        "task": "app.celery_app.task_ingest",
        "schedule": 120.0,
    },
    "train-model-every-15-min": {
        "task": "app.celery_app.task_train",
        "schedule": 15.0*60.0,
    },
}


def make_flask_app():
    from . import create_app
    return create_app()


@celery.task(name="app.celery_app.task_ingest")
def task_ingest():
    app = make_flask_app()
    with app.app_context():
        res = collect_popular_pages(pages=2)
        return res


@celery.task(name="app.celery_app.task_train")
def task_train():
    app = make_flask_app()
    with app.app_context():
        res = train_and_store()
        return res


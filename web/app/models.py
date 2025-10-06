from .db import db
from datetime import datetime


class Movie(db.Model):
    __tablename__ = "movies"
    tmdb_id = db.Column(db.BigInteger, primary_key=True)
    imdb_id = db.Column(db.String(32))
    title = db.Column(db.String(512), nullable=False)
    original_title = db.Column(db.String(512))
    overview = db.Column(db.Text)
    language = db.Column(db.String(16))
    release_date = db.Column(db.Date)
    popularity = db.Column(db.Float)
    vote_count = db.Column(db.Integer)
    vote_average = db.Column(db.Float)
    runtime = db.Column(db.Integer)
    genres = db.Column(db.Text)
    poster_path = db.Column(db.String(256))
    backdrop_path = db.Column(db.String(256))
    inserted_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Snapshot(db.Model):
    __tablename__ = "movie_snapshots"
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    tmdb_id = db.Column(db.BigInteger, db.ForeignKey("movies.tmdb_id"))
    snapshot_ts = db.Column(db.DateTime, nullable=False)
    popularity = db.Column(db.Float)
    vote_count = db.Column(db.Integer)
    vote_average = db.Column(db.Float)


class ModelPrediction(db.Model):
    __tablename__ = "model_predictions"
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    pred_ts = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    tmdb_id = db.Column(db.BigInteger, db.ForeignKey("movies.tmdb_id"))
    model_name = db.Column(db.String(64))
    predicted_popularity = db.Column(db.Float)
    predicted_vote_average = db.Column(db.Float)
    actual_popularity = db.Column(db.Float)
    actual_vote_average = db.Column(db.Float)
    mae_popularity = db.Column(db.Float)
    mae_vote_average = db.Column(db.Float)


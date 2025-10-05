from flask import Blueprint, jsonify
from sqlalchemy import text
from ..db import db
from ..models import ModelPrediction, Movie

api_bp = Blueprint("api", __name__)


@api_bp.get("/summary")
def summary():
    sql = text(
        """
        SELECT m.tmdb_id, m.title, s.popularity, s.vote_count, s.vote_average
        FROM movie_snapshots s
        JOIN movies m ON m.tmdb_id = s.tmdb_id
        WHERE s.snapshot_ts = (
          SELECT MAX(snapshot_ts) FROM movie_snapshots s2 WHERE s2.tmdb_id = s.tmdb_id
        )
        ORDER BY s.popularity DESC
        LIMIT 10
        """
    )
    rows = db.session.execute(sql).mappings().all()
    return jsonify({"top": [dict(row) for row in rows]})


@api_bp.get("/predictions")
def predictions():
    preds = db.session.query(ModelPrediction, Movie.title, Movie.release_date)\
        .join(Movie, Movie.tmdb_id == ModelPrediction.tmdb_id)\
        .filter(ModelPrediction.pred_ts == db.session.query(db.func.max(ModelPrediction.pred_ts)).scalar_subquery())\
        .order_by(ModelPrediction.predicted_popularity.desc())\
        .limit(20)\
        .all()
    
    result = []
    for pred, title, release_date in preds:
        result.append({
            'tmdb_id': pred.tmdb_id,
            'title': title,
            'release_date': str(release_date) if release_date else None,
            'predicted_popularity': pred.predicted_popularity,
            'predicted_vote_average': pred.predicted_vote_average,
            'actual_popularity': pred.actual_popularity,
            'actual_vote_average': pred.actual_vote_average,
            'mae_popularity': pred.mae_popularity,
            'mae_vote_average': pred.mae_vote_average
        })
    
    return jsonify({"predictions": result})


@api_bp.get("/health")
def api_health():
    return {"ok": True}


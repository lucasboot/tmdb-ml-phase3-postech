from flask import Blueprint, jsonify
from sqlalchemy import text
from ..db import db

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


@api_bp.get("/health")
def api_health():
    return {"ok": True}


from flask import Blueprint, jsonify
import json
from sqlalchemy import text
from ..db import db
from ..models import (
    ModelPrediction, 
    Movie,
    HorrorRegression,
    HorrorRegressionPrediction,
    HorrorClassification,
    HorrorClustering,
    HorrorClusterProfile
)

api_bp = Blueprint("api", __name__)


@api_bp.get("/horror/regression/features")
def horror_regression_features():
    latest_ts = db.session.query(db.func.max(HorrorRegression.analysis_ts)).scalar()
    
    if not latest_ts:
        return jsonify({"features": [], "metrics": {}})
    
    features = db.session.query(HorrorRegression)\
        .filter(HorrorRegression.analysis_ts == latest_ts)\
        .order_by(HorrorRegression.feature_importance.desc())\
        .all()
    
    result = {
        "features": [
            {
                "name": f.feature_name,
                "importance": f.feature_importance
            } for f in features
        ],
        "metrics": {
            "mae": features[0].mae if features else 0,
            "r2_score": features[0].r2_score if features else 0
        }
    }
    
    return jsonify(result)


@api_bp.get("/horror/regression/predictions")
def horror_regression_predictions():
    latest_ts = db.session.query(db.func.max(HorrorRegressionPrediction.analysis_ts)).scalar()
    
    if not latest_ts:
        return jsonify({"predictions": []})
    
    preds = db.session.query(HorrorRegressionPrediction, Movie.title)\
        .join(Movie, Movie.tmdb_id == HorrorRegressionPrediction.tmdb_id)\
        .filter(HorrorRegressionPrediction.analysis_ts == latest_ts)\
        .all()
    
    result = {
        "predictions": [
            {
                "title": title,
                "actual": p.actual_popularity,
                "predicted": p.predicted_popularity
            } for p, title in preds
        ]
    }
    
    return jsonify(result)


@api_bp.get("/horror/classification")
def horror_classification():
    latest = db.session.query(HorrorClassification)\
        .order_by(HorrorClassification.analysis_ts.desc())\
        .first()
    
    if not latest:
        return jsonify({"confusion_matrix": [], "roc_curve": {}, "metrics": {}})
    
    result = {
        "confusion_matrix": json.loads(latest.confusion_matrix),
        "roc_curve": json.loads(latest.roc_curve),
        "metrics": {
            "auc": latest.auc_score,
            "accuracy": latest.accuracy
        }
    }
    
    return jsonify(result)


@api_bp.get("/horror/clustering/pca")
def horror_clustering_pca():
    latest_ts = db.session.query(db.func.max(HorrorClustering.analysis_ts)).scalar()
    
    if not latest_ts:
        return jsonify({"clusters": []})
    
    clusters = db.session.query(HorrorClustering, Movie.title)\
        .join(Movie, Movie.tmdb_id == HorrorClustering.tmdb_id)\
        .filter(HorrorClustering.analysis_ts == latest_ts)\
        .all()
    
    result = {
        "clusters": [
            {
                "title": title,
                "cluster_id": c.cluster_id,
                "pca_x": c.pca_x,
                "pca_y": c.pca_y
            } for c, title in clusters
        ]
    }
    
    return jsonify(result)


@api_bp.get("/horror/clustering/profiles")
def horror_clustering_profiles():
    latest_ts = db.session.query(db.func.max(HorrorClusterProfile.analysis_ts)).scalar()
    
    if not latest_ts:
        return jsonify({"profiles": []})
    
    profiles = db.session.query(HorrorClusterProfile)\
        .filter(HorrorClusterProfile.analysis_ts == latest_ts)\
        .order_by(HorrorClusterProfile.cluster_id)\
        .all()
    
    result = {
        "profiles": [
            {
                "cluster_id": p.cluster_id,
                "avg_popularity": p.avg_popularity,
                "avg_vote_average": p.avg_vote_average,
                "avg_runtime": p.avg_runtime,
                "avg_vote_count": p.avg_vote_count,
                "movie_count": p.movie_count
            } for p in profiles
        ]
    }
    
    return jsonify(result)


@api_bp.get("/health")
def api_health():
    return {"ok": True}


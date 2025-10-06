import pandas as pd
import numpy as np
import json
from datetime import datetime
from flask import current_app
from .db import db
from .models import (
    Movie, 
    HorrorRegression, 
    HorrorRegressionPrediction,
    HorrorClassification,
    HorrorClustering,
    HorrorClusterProfile
)
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    mean_absolute_error, 
    r2_score, 
    confusion_matrix, 
    roc_curve, 
    roc_auc_score,
    accuracy_score
)
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA


def get_horror_movies():
    movies = db.session.query(Movie).filter(
        Movie.genres.isnot(None),
        Movie.popularity.isnot(None),
        Movie.vote_average.isnot(None)
    ).all()
    
    horror_movies = [m for m in movies if m.genres and 'Horror' in m.genres]
    return horror_movies


def extract_horror_features(movies_df):
    features = []
    for _, row in movies_df.iterrows():
        feat = {}
        feat['tmdb_id'] = row['tmdb_id']
        feat['runtime'] = row['runtime'] if pd.notna(row['runtime']) and row['runtime'] > 0 else 90
        feat['vote_count'] = row['vote_count'] if pd.notna(row['vote_count']) else 0
        
        if pd.notna(row['release_date']):
            try:
                release = pd.to_datetime(row['release_date'])
                feat['release_year'] = release.year
                feat['release_month'] = release.month
                feat['release_decade'] = (release.year // 10) * 10
                feat['is_october'] = 1 if release.month == 10 else 0
                feat['is_summer'] = 1 if release.month in [6, 7, 8] else 0
                feat['is_holiday'] = 1 if release.month in [11, 12] else 0
            except:
                feat['release_year'] = 2000
                feat['release_month'] = 1
                feat['release_decade'] = 2000
                feat['is_october'] = 0
                feat['is_summer'] = 0
                feat['is_holiday'] = 0
        else:
            feat['release_year'] = 2000
            feat['release_month'] = 1
            feat['release_decade'] = 2000
            feat['is_october'] = 0
            feat['is_summer'] = 0
            feat['is_holiday'] = 0
        
        genres = row['genres'] if pd.notna(row['genres']) else ""
        genre_list = genres.split(',') if genres else []
        feat['genre_count'] = len(genre_list)
        feat['genre_thriller'] = 1 if 'Thriller' in genre_list else 0
        feat['genre_mystery'] = 1 if 'Mystery' in genre_list else 0
        feat['genre_scifi'] = 1 if 'Science Fiction' in genre_list else 0
        feat['genre_fantasy'] = 1 if 'Fantasy' in genre_list else 0
        
        feat['is_english'] = 1 if row['language'] == 'en' else 0
        
        features.append(feat)
    
    return pd.DataFrame(features)


def train_horror_regression():
    horror_movies = get_horror_movies()
    
    if len(horror_movies) < 20:
        return {"trained": False, "reason": "insufficient horror movies"}
    
    movies_df = pd.DataFrame([{
        'tmdb_id': m.tmdb_id,
        'runtime': m.runtime,
        'vote_count': m.vote_count,
        'release_date': m.release_date,
        'genres': m.genres,
        'language': m.language,
        'popularity': m.popularity,
        'vote_average': m.vote_average
    } for m in horror_movies])
    
    features_df = extract_horror_features(movies_df)
    features_df = features_df.merge(movies_df[['tmdb_id', 'popularity', 'vote_average']], on='tmdb_id')
    
    X = features_df.drop(['tmdb_id', 'popularity', 'vote_average'], axis=1)
    y_popularity = features_df['popularity']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y_popularity, test_size=0.25, random_state=42)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
    model.fit(X_train_scaled, y_train)
    
    y_pred = model.predict(X_test_scaled)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    feature_importances = model.feature_importances_
    feature_names = X.columns.tolist()
    
    X_all_scaled = scaler.transform(X)
    y_pred_all = model.predict(X_all_scaled)
    
    analysis_ts = datetime.utcnow()
    
    db.session.query(HorrorRegression).delete()
    db.session.query(HorrorRegressionPrediction).delete()
    
    for feat_name, importance in zip(feature_names, feature_importances):
        hr = HorrorRegression(
            analysis_ts=analysis_ts,
            feature_name=feat_name,
            feature_importance=float(importance),
            mae=float(mae),
            r2_score=float(r2)
        )
        db.session.add(hr)
    
    for idx, tmdb_id in enumerate(features_df['tmdb_id']):
        hrp = HorrorRegressionPrediction(
            analysis_ts=analysis_ts,
            tmdb_id=int(tmdb_id),
            actual_popularity=float(features_df.iloc[idx]['popularity']),
            predicted_popularity=float(y_pred_all[idx])
        )
        db.session.add(hrp)
    
    db.session.commit()
    
    return {
        "trained": True,
        "samples": len(X),
        "mae": float(mae),
        "r2": float(r2)
    }


def train_horror_classification():
    horror_movies = get_horror_movies()
    
    if len(horror_movies) < 20:
        return {"trained": False, "reason": "insufficient horror movies"}
    
    movies_df = pd.DataFrame([{
        'tmdb_id': m.tmdb_id,
        'runtime': m.runtime,
        'vote_count': m.vote_count,
        'release_date': m.release_date,
        'genres': m.genres,
        'language': m.language,
        'popularity': m.popularity,
        'vote_average': m.vote_average
    } for m in horror_movies])
    
    features_df = extract_horror_features(movies_df)
    features_df = features_df.merge(movies_df[['tmdb_id', 'popularity', 'vote_average']], on='tmdb_id')
    
    threshold = features_df['vote_average'].median()
    features_df['high_rating'] = (features_df['vote_average'] > threshold).astype(int)
    
    X = features_df.drop(['tmdb_id', 'popularity', 'vote_average', 'high_rating'], axis=1)
    y = features_df['high_rating']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    model.fit(X_train_scaled, y_train)
    
    y_pred = model.predict(X_test_scaled)
    y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
    
    cm = confusion_matrix(y_test, y_pred)
    accuracy = accuracy_score(y_test, y_pred)
    
    fpr, tpr, thresholds = roc_curve(y_test, y_pred_proba)
    auc = roc_auc_score(y_test, y_pred_proba)
    
    analysis_ts = datetime.utcnow()
    
    db.session.query(HorrorClassification).delete()
    
    hc = HorrorClassification(
        analysis_ts=analysis_ts,
        confusion_matrix=json.dumps(cm.tolist()),
        roc_curve=json.dumps({
            'fpr': fpr.tolist(),
            'tpr': tpr.tolist()
        }),
        auc_score=float(auc),
        accuracy=float(accuracy)
    )
    db.session.add(hc)
    db.session.commit()
    
    return {
        "trained": True,
        "samples": len(X),
        "accuracy": float(accuracy),
        "auc": float(auc)
    }


def train_horror_clustering():
    horror_movies = get_horror_movies()
    
    if len(horror_movies) < 20:
        return {"trained": False, "reason": "insufficient horror movies"}
    
    movies_df = pd.DataFrame([{
        'tmdb_id': m.tmdb_id,
        'runtime': m.runtime,
        'vote_count': m.vote_count,
        'release_date': m.release_date,
        'genres': m.genres,
        'language': m.language,
        'popularity': m.popularity,
        'vote_average': m.vote_average
    } for m in horror_movies])
    
    features_df = extract_horror_features(movies_df)
    features_df = features_df.merge(movies_df[['tmdb_id', 'popularity', 'vote_average']], on='tmdb_id')
    
    X = features_df.drop(['tmdb_id', 'popularity', 'vote_average'], axis=1)
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    n_clusters = min(4, len(X) // 10)
    if n_clusters < 2:
        n_clusters = 2
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X_scaled)
    
    pca = PCA(n_components=2, random_state=42)
    X_pca = pca.fit_transform(X_scaled)
    
    analysis_ts = datetime.utcnow()
    
    db.session.query(HorrorClustering).delete()
    db.session.query(HorrorClusterProfile).delete()
    
    for idx, tmdb_id in enumerate(features_df['tmdb_id']):
        hc = HorrorClustering(
            analysis_ts=analysis_ts,
            tmdb_id=int(tmdb_id),
            cluster_id=int(clusters[idx]),
            pca_x=float(X_pca[idx, 0]),
            pca_y=float(X_pca[idx, 1])
        )
        db.session.add(hc)
    
    for cluster_id in range(n_clusters):
        cluster_mask = clusters == cluster_id
        cluster_data = features_df[cluster_mask]
        
        hcp = HorrorClusterProfile(
            analysis_ts=analysis_ts,
            cluster_id=int(cluster_id),
            avg_popularity=float(cluster_data['popularity'].mean()),
            avg_vote_average=float(cluster_data['vote_average'].mean()),
            avg_runtime=float(cluster_data['runtime'].mean()),
            avg_vote_count=float(cluster_data['vote_count'].mean()),
            movie_count=int(len(cluster_data))
        )
        db.session.add(hcp)
    
    db.session.commit()
    
    return {
        "trained": True,
        "samples": len(X),
        "n_clusters": n_clusters
    }


def train_all_horror_models():
    results = {}
    
    try:
        results['regression'] = train_horror_regression()
    except Exception as e:
        results['regression'] = {"trained": False, "error": str(e)}
    
    try:
        results['classification'] = train_horror_classification()
    except Exception as e:
        results['classification'] = {"trained": False, "error": str(e)}
    
    try:
        results['clustering'] = train_horror_clustering()
    except Exception as e:
        results['clustering'] = {"trained": False, "error": str(e)}
    
    return results

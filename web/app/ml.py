import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from flask import current_app
from .db import db
from .models import Snapshot, Movie, ModelPrediction
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler


def extract_features(movies_df):
    features = []
    for _, row in movies_df.iterrows():
        feat = {}
        feat['tmdb_id'] = row['tmdb_id']
        feat['runtime'] = row['runtime'] if pd.notna(row['runtime']) else 0
        feat['vote_count'] = row['vote_count'] if pd.notna(row['vote_count']) else 0
        
        if pd.notna(row['release_date']):
            try:
                release = pd.to_datetime(row['release_date'])
                feat['release_year'] = release.year
                feat['release_month'] = release.month
                feat['is_summer'] = 1 if release.month in [6, 7, 8] else 0
                feat['is_holiday'] = 1 if release.month in [11, 12] else 0
            except:
                feat['release_year'] = 2020
                feat['release_month'] = 1
                feat['is_summer'] = 0
                feat['is_holiday'] = 0
        else:
            feat['release_year'] = 2020
            feat['release_month'] = 1
            feat['is_summer'] = 0
            feat['is_holiday'] = 0
        
        genres = row['genres'] if pd.notna(row['genres']) else ""
        genre_list = genres.split(',') if genres else []
        feat['genre_action'] = 1 if 'Action' in genre_list else 0
        feat['genre_adventure'] = 1 if 'Adventure' in genre_list else 0
        feat['genre_comedy'] = 1 if 'Comedy' in genre_list else 0
        feat['genre_drama'] = 1 if 'Drama' in genre_list else 0
        feat['genre_scifi'] = 1 if 'Science Fiction' in genre_list else 0
        feat['genre_thriller'] = 1 if 'Thriller' in genre_list else 0
        feat['genre_count'] = len(genre_list)
        
        feat['is_english'] = 1 if row['language'] == 'en' else 0
        
        features.append(feat)
    
    return pd.DataFrame(features)


def train_and_store():
    movies = db.session.query(Movie).filter(Movie.popularity.isnot(None), Movie.vote_average.isnot(None)).all()
    
    if len(movies) < 10:
        return {"trained": False, "reason": "insufficient data"}
    
    movies_df = pd.DataFrame([{
        'tmdb_id': m.tmdb_id,
        'runtime': m.runtime,
        'vote_count': m.vote_count,
        'release_date': m.release_date,
        'genres': m.genres,
        'language': m.language,
        'popularity': m.popularity,
        'vote_average': m.vote_average
    } for m in movies])
    
    features_df = extract_features(movies_df)
    features_df = features_df.merge(movies_df[['tmdb_id', 'popularity', 'vote_average']], on='tmdb_id')
    
    X = features_df.drop(['tmdb_id', 'popularity', 'vote_average'], axis=1)
    y_popularity = features_df['popularity']
    y_vote_avg = features_df['vote_average']
    
    if len(X) < 10:
        return {"trained": False, "reason": "insufficient features"}
    
    X_train, X_test, y_pop_train, y_pop_test = train_test_split(X, y_popularity, test_size=0.25, random_state=42)
    _, _, y_vote_train, y_vote_test = train_test_split(X, y_vote_avg, test_size=0.25, random_state=42)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    model_popularity = LinearRegression()
    model_popularity.fit(X_train_scaled, y_pop_train)
    pred_pop = model_popularity.predict(X_test_scaled)
    mae_pop = mean_absolute_error(y_pop_test, pred_pop)
    r2_pop = r2_score(y_pop_test, pred_pop)
    
    model_vote = LinearRegression()
    model_vote.fit(X_train_scaled, y_vote_train)
    pred_vote = model_vote.predict(X_test_scaled)
    mae_vote = mean_absolute_error(y_vote_test, pred_vote)
    r2_vote = r2_score(y_vote_test, pred_vote)
    
    X_all_scaled = scaler.transform(X)
    pred_all_pop = model_popularity.predict(X_all_scaled)
    pred_all_vote = model_vote.predict(X_all_scaled)
    
    pred_timestamp = datetime.utcnow()
    db.session.query(ModelPrediction).delete()
    
    for idx, tmdb_id in enumerate(features_df['tmdb_id']):
        pred = ModelPrediction(
            pred_ts=pred_timestamp,
            tmdb_id=int(tmdb_id),
            model_name='linear_regression',
            predicted_popularity=float(pred_all_pop[idx]),
            predicted_vote_average=float(pred_all_vote[idx]),
            actual_popularity=float(features_df.iloc[idx]['popularity']),
            actual_vote_average=float(features_df.iloc[idx]['vote_average']),
            mae_popularity=float(mae_pop),
            mae_vote_average=float(mae_vote)
        )
        db.session.add(pred)
    
    db.session.commit()
    
    return {
        "trained": True,
        "samples": len(X),
        "mae_popularity": float(mae_pop),
        "r2_popularity": float(r2_pop),
        "mae_vote_average": float(mae_vote),
        "r2_vote_average": float(r2_vote)
    }


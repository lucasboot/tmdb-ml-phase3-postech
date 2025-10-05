import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from flask import current_app
from .db import db
from .models import Snapshot, Movie, ModelPrediction
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score


def build_dataset(window_days=3, top_n=20):
    cutoff = datetime.utcnow() - timedelta(days=window_days+1)
    q = db.session.query(Snapshot, Movie.title).join(Movie, Movie.tmdb_id==Snapshot.tmdb_id).\
        filter(Snapshot.snapshot_ts >= cutoff)
    df = pd.read_sql(str(q.statement.compile(db.session.bind, compile_kwargs={"literal_binds": True})), db.session.bind)
    if df.empty:
        return None, None
    agg = df.groupby("tmdb_id").agg({
        "popularity": ["last", "mean"],
        "vote_count": ["last", "mean"],
        "vote_average": ["last", "mean"],
    })
    agg.columns = ["_".join(c).strip() for c in agg.columns.values]
    agg = agg.reset_index()
    agg["label"] = 0
    top_idx = agg.sort_values("popularity_last", ascending=False).head(top_n).index
    agg.loc[top_idx, "label"] = 1
    X = agg[["popularity_last","popularity_mean","vote_count_last","vote_count_mean","vote_average_last","vote_average_mean"]]
    y = agg["label"].values
    return X, y


def train_and_store():
    built = build_dataset()
    if built is None or built[0] is None:
        return {"trained": False, "reason": "no data"}
    X, y = built
    if len(np.unique(y)) < 2:
        return {"trained": False, "reason": "only one class"}
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, random_state=42)
    model = LogisticRegression(max_iter=200)
    model.fit(Xtr, ytr)
    auc = float(roc_auc_score(yte, model.predict_proba(Xte)[:,1]))
    probs = model.predict_proba(X)[:,1]
    return {"trained": True, "auc": auc}


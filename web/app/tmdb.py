import os
import time
import requests
from datetime import datetime, timezone
from flask import current_app
from .db import db
from .models import Movie, Snapshot

BASE = "https://api.themoviedb.org/3"


def tmdb_get(path, params=None):
    params = params or {}
    api_key = current_app.config["TMDB_API_KEY"]
    url = f"{BASE}{path}"
    
    if api_key.startswith("eyJ"):
        headers = {"Authorization": f"Bearer {api_key}"}
        r = requests.get(url, params=params, headers=headers, timeout=10)
    else:
        params["api_key"] = api_key
        r = requests.get(url, params=params, timeout=10)
    
    r.raise_for_status()
    return r.json()


def upsert_movie(details):
    genres = None
    if details.get("genres"):
        genres = ",".join([g["name"] for g in details["genres"]])

    m = db.session.get(Movie, details["id"]) or Movie(tmdb_id=details["id"])
    m.imdb_id = details.get("imdb_id")
    m.title = details.get("title") or details.get("name")
    m.original_title = details.get("original_title") or details.get("original_name")
    m.overview = details.get("overview")
    m.language = details.get("original_language")
    rd = details.get("release_date")
    m.release_date = rd if rd in (None, "") else rd
    m.popularity = details.get("popularity")
    m.vote_count = details.get("vote_count")
    m.vote_average = details.get("vote_average")
    m.runtime = details.get("runtime")
    m.genres = genres
    m.poster_path = details.get("poster_path")
    m.backdrop_path = details.get("backdrop_path")

    db.session.add(m)
    return m


def collect_popular_pages(pages=2, sleep_per_call=0.05):
    snapshot_ts = datetime.now(timezone.utc)
    created = 0
    for page in range(1, pages + 1):
        data = tmdb_get("/movie/popular", {"page": page})
        for item in data.get("results", []):
            details = tmdb_get(f"/movie/{item['id']}", {"append_to_response": "credits"})
            m = upsert_movie(details)
            s = Snapshot(
                tmdb_id=m.tmdb_id,
                snapshot_ts=snapshot_ts,
                popularity=details.get("popularity"),
                vote_count=details.get("vote_count"),
                vote_average=details.get("vote_average"),
            )
            db.session.add(s)
            created += 1
            time.sleep(sleep_per_call)
    db.session.commit()
    return {"snapshots": created, "ts": snapshot_ts.isoformat()}


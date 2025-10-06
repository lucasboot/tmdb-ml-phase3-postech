import os
import time
import requests
import logging
from datetime import datetime, timezone
from flask import current_app
from .db import db
from .models import Movie, Snapshot

logger = logging.getLogger(__name__)

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


def create_snapshot(tmdb_id, details, snapshot_ts):
    return Snapshot(
        tmdb_id=tmdb_id,
        snapshot_ts=snapshot_ts,
        popularity=details.get("popularity"),
        vote_count=details.get("vote_count"),
        vote_average=details.get("vote_average"),
    )


def fetch_and_process_movie(movie_id, snapshot_ts, sleep_time=0.1):
    details = tmdb_get(f"/movie/{movie_id}", {"append_to_response": "credits"})
    movie = upsert_movie(details)
    snapshot = create_snapshot(movie.tmdb_id, details, snapshot_ts)
    db.session.add(snapshot)
    
    if sleep_time > 0:
        time.sleep(sleep_time)
    
    return movie, snapshot


def collect_popular_pages(pages=2, sleep_per_call=0.1):
    snapshot_ts = datetime.now(timezone.utc)
    created = 0
    
    for page in range(1, pages + 1):
        data = tmdb_get("/movie/popular", {"page": page})
        for item in data.get("results", []):
            fetch_and_process_movie(item['id'], snapshot_ts, sleep_per_call)
            created += 1
    
    db.session.commit()
    logger.info(f"Collected {created} popular movies")
    return {"snapshots": created, "ts": snapshot_ts.isoformat()}


def _discover_movies_for_year(year, min_votes, max_pages, snapshot_ts, sleep_per_call):
    movies_count = 0
    page = 1
    
    while page <= max_pages:
        try:
            data = tmdb_get("/discover/movie", {
                "primary_release_year": year,
                "page": page,
                "sort_by": "popularity.desc",
                "vote_count.gte": min_votes
            })
            
            results = data.get("results", [])
            if not results:
                break
            
            for item in results:
                try:
                    fetch_and_process_movie(item['id'], snapshot_ts, sleep_per_call)
                    movies_count += 1
                except Exception as e:
                    logger.warning(f"Failed to process movie {item.get('id')}: {e}")
                    continue
            
            db.session.commit()
            
            if page >= data.get("total_pages", 0):
                break
            
            page += 1
            
        except Exception as e:
            logger.error(f"Failed to fetch page {page} for year {year}: {e}")
            break
    
    return movies_count


def initial_ingest_movies(start_year=2010, end_year=None, min_votes=50, max_pages_per_year=50, sleep_per_call=0.1):
    if end_year is None:
        end_year = datetime.now().year
    
    start_time = time.time()
    snapshot_ts = datetime.now(timezone.utc)
    total_movies = 0
    
    logger.info(f"Starting initial ingest: {start_year}-{end_year}, min_votes={min_votes}")
    
    for year in range(start_year, end_year + 1):
        year_movies = _discover_movies_for_year(year, min_votes, max_pages_per_year, snapshot_ts, sleep_per_call)
        total_movies += year_movies
        logger.info(f"Year {year}: {year_movies} movies collected (total: {total_movies})")
    
    duration = time.time() - start_time
    logger.info(f"Initial ingest completed: {total_movies} movies in {duration/60:.1f}m")
    
    return {
        "total_movies": total_movies,
        "total_snapshots": total_movies,
        "years_processed": end_year - start_year + 1,
        "start_year": start_year,
        "end_year": end_year,
        "min_votes": min_votes,
        "duration_minutes": round(duration / 60, 2),
        "ts": snapshot_ts.isoformat()
    }


def _discover_movies_for_year_with_genre(year, genre_id, min_votes, max_pages, snapshot_ts, sleep_per_call):
    movies_count = 0
    page = 1
    
    while page <= max_pages:
        try:
            data = tmdb_get("/discover/movie", {
                "primary_release_year": year,
                "with_genres": genre_id,
                "page": page,
                "sort_by": "popularity.desc",
                "vote_count.gte": min_votes
            })
            
            results = data.get("results", [])
            if not results:
                break
            
            for item in results:
                try:
                    fetch_and_process_movie(item['id'], snapshot_ts, sleep_per_call)
                    movies_count += 1
                except Exception as e:
                    logger.warning(f"Failed to process movie {item.get('id')}: {e}")
                    continue
            
            db.session.commit()
            
            if page >= data.get("total_pages", 0):
                break
            
            page += 1
            
        except Exception as e:
            logger.error(f"Failed to fetch page {page} for year {year}: {e}")
            break
    
    return movies_count


def collect_movies_by_year_range(start_year=2025, end_year=None, max_pages_per_year=20, sleep_per_call=0.1):
    if end_year is None:
        end_year = datetime.now().year
    
    start_time = time.time()
    snapshot_ts = datetime.now(timezone.utc)
    total_movies = 0
    
    logger.info(f"Collecting horror movies: {start_year}-{end_year}")
    
    for year in range(start_year, end_year + 1):
        year_movies = _discover_movies_for_year_with_genre(year, 27, 10, max_pages_per_year, snapshot_ts, sleep_per_call)
        total_movies += year_movies
        logger.info(f"Year {year}: {year_movies} horror movies (total: {total_movies})")
    
    duration = time.time() - start_time
    logger.info(f"Collection completed: {total_movies} movies in {duration/60:.1f}m")
    
    return {
        "total_movies": total_movies,
        "total_snapshots": total_movies,
        "years_processed": end_year - start_year + 1,
        "start_year": start_year,
        "end_year": end_year,
        "genre": "Horror",
        "duration_minutes": round(duration / 60, 2),
        "ts": snapshot_ts.isoformat()
    }


def _update_recent_years(years, existing_ids, min_votes, max_pages, snapshot_ts, sleep_per_call):
    new_count = 0
    updated_count = 0
    
    for year in years:
        page = 1
        while page <= max_pages:
            try:
                data = tmdb_get("/discover/movie", {
                    "primary_release_year": year,
                    "page": page,
                    "sort_by": "popularity.desc",
                    "vote_count.gte": min_votes
                })
                
                results = data.get("results", [])
                if not results:
                    break
                
                for item in results:
                    try:
                        movie_id = item.get('id')
                        is_new = movie_id not in existing_ids
                        
                        fetch_and_process_movie(movie_id, snapshot_ts, sleep_per_call)
                        
                        if is_new:
                            new_count += 1
                            existing_ids.add(movie_id)
                        else:
                            updated_count += 1
                            
                    except Exception as e:
                        logger.warning(f"Failed to process movie {item.get('id')}: {e}")
                        continue
                
                db.session.commit()
                page += 1
                
            except Exception as e:
                logger.error(f"Failed to fetch page {page} for year {year}: {e}")
                break
    
    return new_count, updated_count


def _update_oldest_movies(limit, snapshot_ts, sleep_per_call):
    movies = db.session.query(Movie).order_by(Movie.updated_at.asc()).limit(limit).all()
    updated = 0
    
    for movie in movies:
        try:
            fetch_and_process_movie(movie.tmdb_id, snapshot_ts, sleep_per_call)
            updated += 1
        except Exception as e:
            logger.warning(f"Failed to update movie {movie.tmdb_id}: {e}")
            continue
    
    db.session.commit()
    return updated


def update_movies_incremental(min_votes=50, max_pages=5, sleep_per_call=0.1):
    start_time = time.time()
    snapshot_ts = datetime.now(timezone.utc)
    current_year = datetime.now().year
    
    existing_ids = {movie[0] for movie in db.session.query(Movie.tmdb_id).all()}
    logger.info(f"Incremental update started. DB has {len(existing_ids)} movies")
    
    years_to_check = [current_year, current_year - 1]
    new_movies, updated_recent = _update_recent_years(
        years_to_check, existing_ids, min_votes, max_pages, snapshot_ts, sleep_per_call
    )
    
    updated_old = _update_oldest_movies(20, snapshot_ts, sleep_per_call)
    total_updated = updated_recent + updated_old
    
    duration = time.time() - start_time
    logger.info(f"Update completed: {new_movies} new, {total_updated} updated in {duration:.1f}s")
    
    return {
        "new_movies": new_movies,
        "updated_movies": total_updated,
        "total_snapshots": new_movies + total_updated,
        "duration_seconds": round(duration, 2),
        "ts": snapshot_ts.isoformat()
    }


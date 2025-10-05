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


def collect_movies_by_year_range(start_year=2024, end_year=None, max_pages_per_year=20, sleep_per_call=0.3):
    if end_year is None:
        end_year = datetime.now().year
    
    start_time = time.time()
    snapshot_ts = datetime.now(timezone.utc)
    total_movies = 0
    total_snapshots = 0
    years_processed = 0
    total_years = end_year - start_year + 1
    
    print("=" * 80)
    print(f"🎬 INICIANDO COLETA DE FILMES DE TERROR/HORROR")
    print("=" * 80)
    print(f"Período: {start_year} - {end_year} ({total_years} anos)")
    print(f"Páginas por ano: {max_pages_per_year} (~{max_pages_per_year * 20} filmes/ano)")
    print(f"Delay entre requisições: {sleep_per_call}s")
    print(f"Timestamp: {snapshot_ts.isoformat()}")
    print("=" * 80)
    print()
    
    for year in range(start_year, end_year + 1):
        year_start_time = time.time()
        years_processed += 1
        year_movies = 0
        
        progress_pct = ((years_processed - 1) / total_years) * 100
        print(f"📅 ANO {year} - Progresso geral: {progress_pct:.1f}% ({years_processed}/{total_years} anos)")
        print("-" * 80)
        
        for page in range(1, max_pages_per_year + 1):
            try:
                print(f"  📄 Página {page}/{max_pages_per_year}...", end=" ", flush=True)
                
                data = tmdb_get("/discover/movie", {
                    "primary_release_year": year,
                    "with_genres": 27,
                    "page": page,
                    "sort_by": "popularity.desc",
                    "vote_count.gte": 10
                })
                
                results = data.get("results", [])
                total_pages = data.get("total_pages", 0)
                
                if not results:
                    print("sem resultados")
                    break
                
                print(f"{len(results)} filmes encontrados")
                
                for idx, item in enumerate(results, 1):
                    try:
                        movie_id = item.get('id')
                        movie_title = item.get('title', 'Sem título')
                        
                        details = tmdb_get(f"/movie/{movie_id}", {"append_to_response": "credits"})
                        m = upsert_movie(details)
                        
                        s = Snapshot(
                            tmdb_id=m.tmdb_id,
                            snapshot_ts=snapshot_ts,
                            popularity=details.get("popularity"),
                            vote_count=details.get("vote_count"),
                            vote_average=details.get("vote_average"),
                        )
                        db.session.add(s)
                        year_movies += 1
                        total_snapshots += 1
                        
                        print(f"    ✅ [{idx:2d}/20] {movie_title[:50]} (ID: {movie_id})")
                        
                        time.sleep(sleep_per_call)
                    except Exception as e:
                        print(f"    ❌ Erro ao processar filme {item.get('id')}: {e}")
                        continue
                
                db.session.commit()
                print(f"    💾 Página {page} salva no banco ({year_movies} filmes até agora em {year})")
                
                if page >= total_pages:
                    print(f"  ℹ️  Última página disponível alcançada ({total_pages} páginas totais)")
                    break
                    
            except Exception as e:
                print(f"\n  ❌ Erro ao coletar página {page} do ano {year}: {e}")
                break
        
        year_duration = time.time() - year_start_time
        total_movies += year_movies
        
        print()
        print(f"✅ ANO {year} CONCLUÍDO: {year_movies} filmes coletados em {year_duration:.1f}s")
        
        elapsed_time = time.time() - start_time
        avg_time_per_year = elapsed_time / years_processed
        remaining_years = total_years - years_processed
        estimated_remaining = avg_time_per_year * remaining_years
        
        print(f"📊 Total acumulado: {total_movies} filmes")
        print(f"⏱️  Tempo decorrido: {elapsed_time/60:.1f} min | Estimado restante: {estimated_remaining/60:.1f} min")
        print("=" * 80)
        print()
    
    total_duration = time.time() - start_time
    
    print()
    print("=" * 80)
    print("🎉 COLETA FINALIZADA COM SUCESSO!")
    print("=" * 80)
    print(f"Total de filmes coletados: {total_movies}")
    print(f"Total de snapshots criados: {total_snapshots}")
    print(f"Anos processados: {years_processed} ({start_year}-{end_year})")
    print(f"Tempo total: {total_duration/60:.1f} minutos ({total_duration/3600:.2f} horas)")
    print(f"Média: {total_movies/years_processed:.1f} filmes/ano | {total_duration/total_movies:.2f}s/filme")
    print(f"Timestamp: {snapshot_ts.isoformat()}")
    print("=" * 80)
    
    return {
        "total_movies": total_movies,
        "total_snapshots": total_snapshots,
        "years_processed": years_processed,
        "start_year": start_year,
        "end_year": end_year,
        "genre": "Horror",
        "duration_minutes": round(total_duration / 60, 2),
        "ts": snapshot_ts.isoformat()
    }


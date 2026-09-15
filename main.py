from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
import requests
import os

app = FastAPI()

TMDB_API_KEY = "1108288019c102eb67856affb97d19f7"

# 여러 개의 영화 ID를 받을 데이터 모델 정의
class MovieSelection(BaseModel):
    movie_ids: List[int]

@app.get("/", response_class=HTMLResponse)
async def read_index():
    file_path = os.path.join("templates", "index.html")
    with open(file_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.get("/api")
def read_root():
  return JSONResponse(
      content={"message": "영화 추천 서버가 정상적으로 작동 중입니다!"},
      media_type="application/json; charset=utf-8",
  )

@app.get("/search")
def search_movie(query: str = ""):
    if not query.strip():
        return JSONResponse(content={"results": []}, media_type="application/json; charset=utf-8")

    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&language=ko-KR&query={query}"
    response = requests.get(url)
    data = response.json()

    movies = []
    for item in data.get("results", []):

        overview = item.get("overview")
        if overview is None:
            continue

        overview_str = str(overview).strip()

        if not overview_str or len(overview_str) < 5:
            continue
        movies.append({
            "id": item.get("id"),
            "title": item.get("title"),
            "release_date": item.get("release_date"),
            "overview": overview_str,
            "poster_path": (
                f"https://image.tmdb.org/t/p/w500{item.get('poster_path')}"
                if item.get("poster_path")
                else None
            ),
        })

    return JSONResponse(content={"results": movies}, media_type="application/json; charset=utf-8")

# 여러 영화 ID를 받아 비슷한 영화들을 종합 추천해주는 API
@app.post("/recommend")
def recommend_multiple_movies(selection: MovieSelection):
    all_movies = {}
    
    for movie_id in selection.movie_ids:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}/similar?api_key={TMDB_API_KEY}&language=ko-KR"
        response = requests.get(url)
        data = response.json()
        
        for item in data.get("results", []):
            m_id = item.get("id")
            overview = item.get("overview")

            if overview is None:
                continue

            overview_str = str(overview).strip()

            if not overview_str or len(overview_str) < 5:
                continue
            # 사용자가 선택한 원본 영화이거나 이미 담긴 영화가 아니면 추가 (중복 제거)
            if m_id not in selection.movie_ids and m_id not in all_movies:
                all_movies[m_id] = {
                    "id": m_id,
                    "title": item.get("title"),
                    "release_date": item.get("release_date"),
                    "overview": overview_str,
                    "poster_path": (
                        f"https://image.tmdb.org/t/p/w500{item.get('poster_path')}"
                        if item.get("poster_path")
                        else None
                    ),
                }

    return JSONResponse(
        content={"results": list(all_movies.values())},
        media_type="application/json; charset=utf-8",
    )






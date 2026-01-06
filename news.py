from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import asyncio
from scrapers import get_all_news

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "News Scraper API is running. Go to /ui to see the dashboard."}

@app.get("/ui")
async def read_index():
    from fastapi.responses import FileResponse
    return FileResponse('index.html')

class NewsItem(BaseModel):
    title: str
    summary: str
    url: str
    image: Optional[str] = None
    source: str
    published_at: Optional[str] = None

@app.get("/news", response_model=List[NewsItem])
async def news():
    news_items = await get_all_news()
    # Deduplicate by URL
    seen_urls = set()
    unique_news = []
    for item in news_items:
        if item['url'] not in seen_urls:
            unique_news.append(item)
            seen_urls.add(item['url'])
    return unique_news

@app.get("/news/{source_id}", response_model=List[NewsItem])
async def news_by_source(source_id: str):
    from scrapers import get_news_by_source_id
    news_items = await get_news_by_source_id(source_id)
    return news_items

@app.get("/sources")
def list_sources():
    from scrapers import SCRAPER_CONFIG
    return [{"id": key, "name": val["name"]} for key, val in SCRAPER_CONFIG.items()]


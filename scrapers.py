import asyncio
import feedparser
import httpx
from bs4 import BeautifulSoup
from typing import List, Optional
from datetime import datetime
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsItem:
    def __init__(self, title, summary, url, image, source, published_at):
        self.title = title
        self.summary = summary
        self.url = url
        self.image = image
        self.source = source
        self.published_at = published_at

    def to_dict(self):
        return {
            "title": self.title,
            "summary": self.summary,
            "url": self.url,
            "image": self.image,
            "source": self.source,
            "published_at": self.published_at
        }

# Configuration for all scrapers
SCRAPER_CONFIG = {
    "geo_tv": {
        "type": "html",
        "url": "https://www.geo.tv/",
        "name": "Geo TV",
        "default_image": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Geo_TV_logo.svg/1200px-Geo_TV_logo.svg.png",
        "selectors": {
            'article_container': 'div.m_c_left ul li, div.m_c_right ul li article',
            'title': '.heading h1, .heading h2',
            'summary': '.m_except p',
            'image': '.m_pic img'
        }
    },
    "bbc_news": {
        "type": "rss",
        "url": "http://feeds.bbci.co.uk/news/rss.xml",
        "name": "BBC News",
        "default_image": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/62/BBC_News_2019.svg/1200px-BBC_News_2019.svg.png"
    },
    "cnn": {
        "type": "rss",
        "url": "http://rss.cnn.com/rss/edition.rss",
        "name": "CNN",
        "default_image": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/66/CNN_International_logo.svg/1200px-CNN_International_logo.svg.png"
    },
    "pakistan_point": {
        "type": "html",
        "url": "https://www.pakistanpoint.com/en/",
        "name": "Pakistan Point",
        "default_image": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/52/Pakistan_Point_Logo.png/800px-Pakistan_Point_Logo.png",
        "selectors": {
            'article_container': 'div[class*="lfw1_"], div[class*="lfw2_"], div[class*="bwn_list"], div[class*="bwn_rlist"]',
            'title': 'h3, p',  
            'summary': '', 
            'image': 'img'
        }
    },

    "trt_world": {
        "type": "html",
        "url": "https://www.trtworld.com/news",
        "name": "TRT World",
        "default_image": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/TRT_World_Logo.svg/1200px-TRT_World_Logo.svg.png",
        "selectors": {
            'article_container': 'div[data-testid="single-card"]',
            'title': 'div[data-testid="headline:title"] span',
            'summary': 'div[data-testid="headline:description"] span',
            'image': 'div[data-testid="media:desktop"] img, div[data-testid="media:mobile"] img',
            'link_selector': 'a[href*="/article/"]'
        }
    },
    "middle_east_eye": {
        "type": "rss",
        "url": "https://middleeasteye.net/rss",
        "name": "Middle East Eye",
        "default_image": "https://upload.wikimedia.org/wikipedia/commons/9/9e/Middle_East_Eye_logo.png"
    }
}

async def fetch_rss(url, source_name, default_image=None):
    """Fetches and parses an RSS feed."""
    items = []
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0, follow_redirects=True)
            if response.status_code == 200:
                feed = feedparser.parse(response.text)
                for entry in feed.entries:
                    # Extract image
                    image = None

                    if 'media_content' in entry:
                        image = entry.media_content[0]['url']
                    elif 'media_thumbnail' in entry:
                        image = entry.media_thumbnail[0]['url']
                    elif 'links' in entry:
                         for link in entry.links:
                             if link.get('type', '').startswith('image/'):
                                 image = link['href']
                                 break
                    
                    # Fallback: try to find img tag in summary/content
                    if not image:
                        content_to_check = entry.get('summary', '') or entry.get('content', [{'value': ''}])[0]['value']
                        if content_to_check:
                            soup = BeautifulSoup(content_to_check, 'lxml')
                            img_tag = soup.find('img')
                            if img_tag:
                                image = img_tag.get('src')
                    
                    published = entry.get('published', entry.get('updated', str(datetime.now())))
                    
                    # Cleanup summary -> remove HTML tags
                    raw_summary = entry.get('summary', '') or entry.get('description', '')
                    summary_soup = BeautifulSoup(raw_summary, 'lxml')
                    summary_text = summary_soup.get_text(strip=True)[:300] + '...' if len(summary_soup.get_text(strip=True)) > 300 else summary_soup.get_text(strip=True)

                    items.append(NewsItem(
                        title=entry.title,
                        summary=summary_text,
                        url=entry.link,
                        image=image or default_image,
                        source=source_name,
                        published_at=published
                    ))
    except Exception as e:
        logger.error(f"Error fetching RSS from {source_name}: {e}")
    return items

async def fetch_html_generic(url, source_name, selectors, default_image=None):
    """Fetches HTML and scrapes using CSS selectors."""
    items = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        async with httpx.AsyncClient(follow_redirects=True, verify=False) as client:
            response = await client.get(url, headers=headers, timeout=15.0)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'lxml')
                articles = soup.select(selectors['article_container'])
                
                logger.info(f"Found {len(articles)} articles for {source_name}")

                for article in articles[:15]: # Limit to 15 items per source
                    try:
                        title_tag = article.select_one(selectors['title'])
                        if not title_tag:
                            continue
                        title = title_tag.get_text(strip=True)
                        
                        link = url
                        if selectors.get('link_selector'):
                             link_tag = article.select_one(selectors['link_selector'])
                             if link_tag:
                                 href = link_tag.get('href')
                             else:
                                 href = None
                        elif title_tag.name == 'a':
                            href = title_tag.get('href')
                        elif title_tag.find_parent('a'):
                             href = title_tag.find_parent('a').get('href')
                        else:
                            # Try finding any a tag
                            a_tag = article.find('a')
                            href = a_tag.get('href') if a_tag else None

                        if href:
                            if href.startswith('http'):
                                link = href
                            elif href.startswith('//'):
                                link = 'https:' + href
                            else:
                                link = url.rstrip('/') + '/' + href.lstrip('/')
                        else:
                            continue # No link, skip
                        
                        summary = ""
                        if selectors.get('summary'):
                            summary_tag = article.select_one(selectors['summary'])
                            if summary_tag:
                                summary = summary_tag.get_text(strip=True)
                        
                        image = None
                        if selectors.get('image'):
                            img_tag = article.select_one(selectors['image'])
                            if img_tag:
                                # Prioritize data-src for lazy loading
                                image = img_tag.get('data-src') or img_tag.get('src')
                                if image:
                                    image = image.strip()
                                    if image.startswith('http'):
                                        pass
                                    elif image.startswith('//'):
                                        image = 'https:' + image
                                    else:
                                        # Handle relative paths carefully
                                        base_url = '/'.join(url.split('/')[:3]) # https://site.com
                                        if image.startswith('/'):
                                            image = base_url + image
                                        else:
                                            image = base_url + '/' + image

                        published_at = str(datetime.now())
                        
                        items.append(NewsItem(
                            title=title,
                            summary=summary,
                            url=link,
                            image=image or default_image,
                            source=source_name,
                            published_at=published_at
                        ))
                    except Exception as e:
                        # logger.error(f"Error parsing article for {source_name}: {e}")
                        continue
    except Exception as e:
        logger.error(f"Error scraping {source_name}: {e}")
    return items

async def get_news_from_source(config):
    """Helper to call correct fetcher based on config."""
    if config['type'] == 'rss':
        return await fetch_rss(config['url'], config['name'], config.get('default_image'))
    elif config['type'] == 'html':
        return await fetch_html_generic(config['url'], config['name'], config['selectors'], config.get('default_image'))
    return []

async def get_all_news():
    tasks = []
    for key, config in SCRAPER_CONFIG.items():
        tasks.append(get_news_from_source(config))

    results = await asyncio.gather(*tasks)
    
    # Flatten list
    flat_results = [item.to_dict() for sublist in results for item in sublist]
    return flat_results

async def get_news_by_source_id(source_id):
    if source_id not in SCRAPER_CONFIG:
        return []
    
    config = SCRAPER_CONFIG[source_id]
    items = await get_news_from_source(config)
    return [item.to_dict() for item in items]

import asyncio
import httpx
import feedparser
from bs4 import BeautifulSoup
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_feed(url, name):
    print(f"\n--- Debugging {name} ---")
    async with httpx.AsyncClient() as client:
        response = await client.get(url, follow_redirects=True)
        if response.status_code == 200:
            feed = feedparser.parse(response.text)
            if not feed.entries:
                print("No entries found.")
                return

            entry = feed.entries[0]
            print(f"Title: {entry.title}")
            
            # Check standard fields
            print(f"Media Content: {entry.get('media_content')}")
            print(f"Media Thumbnail: {entry.get('media_thumbnail')}")
            print(f"Links: {entry.get('links')}")
            
            # Check content for img tags
            content = entry.get('summary', '') or entry.get('description', '')
            if 'content' in entry:
                content += str(entry.content)
            
            soup = BeautifulSoup(content, 'lxml')
            img = soup.find('img')
            print(f"Found img tag in content: {img}")
        else:
            print(f"Failed to fetch: {response.status_code}")

async def main():
    # await debug_feed("https://feeds.washingtonpost.com/rss/world", "Washington Post")
    await debug_feed("https://news.google.com/rss/search?q=site:reuters.com", "Reuters (Google)")
    await debug_feed("https://www.aljazeera.com/xml/rss/all.xml", "Al Jazeera")

if __name__ == "__main__":
    asyncio.run(main())

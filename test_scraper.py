import asyncio
from scrapers import get_all_news
import logging

# Configure logging to see output
logging.basicConfig(level=logging.INFO)

async def main():
    print("Starting scraping...")
    items = await get_all_news()
    print(f"Scraped {len(items)} items.")
    for item in items[:20]:
        print(f"[{item['source']}] {item['title']} - {item['url']}")

if __name__ == "__main__":
    asyncio.run(main())

import asyncio

from crawl4ai import AsyncWebCrawler
from dotenv import load_dotenv

from config import BASE_URL, CSS_SELECTOR, REQUIRED_KEYS
from utils.data_utils import save_venue_to_csv

from utils.scraper_utils import fetch_and_process_page, get_browser_config, get_llm_strategy


load_dotenv()


async def crawl_venues():
    
    browser_config = get_browser_config()
    llm_strategy = get_llm_strategy()
    sessio_id = "Venue_crawler_session"
    
    page_number = 1
    all_venues = []
    seen_names = set()
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        while True:
            venues, no_results_found = await fetch_and_process_page(
                crawler,
                page_number,
                BASE_URL,
                CSS_SELECTOR,
                llm_strategy,
                sessio_id,
                REQUIRED_KEYS,
                seen_names
            )
            
            if no_results_found:
                print("No more results found. Ending the crawl.")  
                break
            
            if not venues:
                print("No vehicle adds found on page.")
                break
            
            all_venues.extend(venues)
            page_number += 1
            
            await asyncio.sleep(3)
            
        if all_venues:
            save_venue_to_csv(all_venues, "complete_add_details.csv")
            print(f"Saved {len(all_venues)} vehciles to CSV.")
            
        else:
            print("No adds found.")
            
        llm_strategy.show_usage()
        
async def main():
    await crawl_venues()
    
if __name__ == "__main__":
    asyncio.run(main())
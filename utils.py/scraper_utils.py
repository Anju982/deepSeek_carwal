import json
import os
from typing import List, Set, Tuple

from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig, LLMExtractionStrategy

from models.venue import Venue
from data_utils import is_complete_venue, is_duplicate_vanue

def get_browser_config() -> BrowserConfig:
    return BrowserConfig(
        browser_type="firefox",
        headless=False,
        verbose=True,
        text_mode=True,
        light_mode=True
    )
    
def get_llm_strategy() -> LLMExtractionStrategy:
    return LLMExtractionStrategy(
        provider="groq/deepseek-r1-distill-llama-70b",
        api_token= os.getenv("groq_api_key"),
        schema=Venue.model_json_schema(),
        extraction_type="schema",
        instruction=(
            "Extract all venue objects with 'name', 'location', 'price', 'capacity', "
            "'rating', 'reviews', and a 1 sentence description of the venue from the "
            "following content."
        ),
        input_format="markdown",
        verbose=True,
    )
    
async def check_no_results(
    crawler: AsyncWebCrawler,
    url: str,
    session_id: str,
) -> bool:
    result = await crawler.arun(
        url=url,
        config=CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            session_id=session_id,
        ),
    )
    
    if result.success:
        if "No results found" in result.cleaned_html:
            return True
        else:
            print(f"No results found message not found: {result.error_message}")
        
        return False
    
async def fetch_and_process_page(
    crawler: AsyncWebCrawler,
    page_number: int,
    base_url: str,
    css_selector: str,
    llm_strategy: LLMExtractionStrategy,
    session_id: str,
    required_keys: List[str],
    seen_names: Set[str],
) -> Tuple[List[dict], bool]:
    
    url = f"{base_url}?page={page_number}"
    print(f"Fetching {url}")
    
    no_results = await check_no_results(crawler, url, session_id)
    if no_results:
        return [], True
    
    result = await crawler.arun(
        url=url,
        config=CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=llm_strategy,
            css_selector=css_selector,
            session_id=session_id,
        ),
    )
    
    if not (result.success and result.extracted_content):
        print(f"Failed to fetch page {page_number}: {result.error_message}")
        return [], False
    
    # Parese extracted content
    extracted_content = json.loads(result.extracted_content)
    
    if not extracted_content:
        print(f"No venues found on page {page_number}")
        return [], False
    
    print("Extracted content:", extracted_content)
    
    #Process_venues
    
    complete_venues = []
    for venue in extracted_content:
        print("Processing venue:", venue)
        
        if venue.get("error") is False:
            venue.pop("error", None)
            
        if not is_complete_venue(venue, required_keys):
            continue
        
        if is_duplicate_vanue(venue["name"], seen_names):
            print(f"Duplicate venue found: {venue['name']}")
            continue
        
        seen_names.add(venue["name"])
        complete_venues.append(venue)
        
    if not complete_venues:
        print(f"No complete venues found on page {page_number}")
        return [], False
    
    print(f"Extracted {len(complete_venues)} venues from page {page_number}")
    return complete_venues, False
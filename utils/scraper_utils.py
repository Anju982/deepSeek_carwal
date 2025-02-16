import json
import os
from typing import List, Set, Tuple
import time
import random

from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig, LLMExtractionStrategy, DefaultMarkdownGenerator

from models.vehicle import Vehicle
from utils.data_utils import is_complete_details

def get_browser_config() -> BrowserConfig:
    return BrowserConfig(
        browser_type="firefox",
        headless=True,
        verbose=True,
        text_mode=True,
        light_mode=True
    )
    
def get_llm_strategy() -> LLMExtractionStrategy:
    return LLMExtractionStrategy(
        provider="huggingface/mistralai/Mixtral-8x7B-Instruct-v0.1",
        api_token=os.getenv("hf_key"),
        schema=Vehicle.model_json_schema(),
        extraction_type="schema",
        instruction=(
            "Extract all car listings with the following attributes:\n"
            "- 'name': The car's make and model.\n"
            "- 'location': The city or town where the car is listed.\n"
            "- 'price': The listed price of the car.\n"
            "- 'mileage': The number of kilometers driven.\n"
            "- 'date': The date of the listing.\n"
        ),
        input_format="markdown",
        verbose=True,
        chunk_token_threshold=100,
        overlap_rate=0.1,
        apply_chunking=True,
        #extra_args={
            #"max_tokens": 6000,
            #temperature": 0.1,
        #}
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
    
    if page_number == 1:
        url = base_url
    else:
        url = f"{base_url}?page={page_number}"
    print(f"Fetching {url}")
    
    no_results = await check_no_results(crawler, url, session_id)
    if no_results:
        return [], True
    
    result = await crawler.arun(
        url=url,
        config=CrawlerRunConfig(
            #word_count_threshold=1000,
            markdown_generator=DefaultMarkdownGenerator(
                options={
                            "ignore_links": True,
                            "escape_html": False,
                            "body_width": 80
                }
                ),
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=llm_strategy,
            session_id=session_id,
            css_selector=css_selector, 
        ),
    )
    
    if not (result.success and result.extracted_content):
        print(f"Failed to fetch page {page_number}: {result.error_message}")
        return [], False
    
    # Parese extracted content
    extracted_content = json.loads(result.extracted_content)
    
    if not extracted_content:
        print(f"No Vehicle add found on page {page_number}")
        return [], False
    
    print("Extracted content:", extracted_content)
    
    #Process_venues
    
    complete_details = []
    for venue in extracted_content:
        print("Processing details:", venue)
        
        if venue.get("error") is False:
            venue.pop("error", None)
            
        if not is_complete_details(venue, required_keys):
            continue
        
        seen_names.add(venue["name"])
        complete_details.append(venue)
        
    if not complete_details:
        print(f"No data found on page {page_number}")
        return [], False
    
    print(f"Extracted {len(complete_details)} adds from page {page_number}")
    return complete_details, False
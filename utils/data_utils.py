import csv
from models.venue import Venue

def is_duplicate_vanue(venue_name: str, seen_names:set) -> bool:
    return venue_name in seen_names

def is_complete_venue(venue: dict, required_keys: list) -> bool:
    return all(key in venue for key in required_keys)

def save_venue_to_csv(venues: list, file_name: str):
    if not venues:
        print("No venues to save")
        return
    
    fieldNames = Venue.model_fields.keys()
    
    
    with open(file_name, mode='w', newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldNames)
        writer.writeheader()
        writer.writerows(venues)
        
    print(f"Saved {len(venues)} venues to {file_name}")
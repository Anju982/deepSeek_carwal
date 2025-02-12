import csv
from models.vehicle import Vehicle


def is_complete_details(vehicle: dict, required_keys: list) -> bool:
    return all(key in vehicle for key in required_keys)

def save_venue_to_csv(vehicles: list, file_name: str):
    if not vehicles:
        print("No vehicles add to save")
        return
    
    fieldNames = Vehicle.model_fields.keys()
    
    
    with open(file_name, mode='w', newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldNames)
        writer.writeheader()
        writer.writerows(vehicles)
        
    print(f"Saved {len(vehicles)} venues to {file_name}")
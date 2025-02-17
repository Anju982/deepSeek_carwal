import csv
from models.vehicle import Vehicle
import mysql.connector
from datetime import datetime
import os


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
    
def save_to_db(vehicles: list):
    if not vehicles:
        print("No vehicles to save")
        return

    connection = mysql.connector.connect(
        host=os.getenv("mysqlhost"),
        user=os.getenv("mysqluser"),
        password=os.getenv("mysqlpassword"),
        database=os.getenv("database")
    )
    
    try:
        cursor = connection.cursor()
        scrape_date = datetime.now().strftime("%Y-%m-%d")
        
        for vehicle in vehicles:
            # Clean and convert price to proper format
            price = vehicle['price']
            if isinstance(price, str):
                price = ''.join(c for c in price if c.isdigit() or c == '.')
                try:
                    price = float(price)
                except ValueError:
                    price = 0.0

            # Clean and convert mileage to proper format
            mileage = vehicle['mileage']
            if isinstance(mileage, str):
                # Extract numbers from mileage string
                mileage_nums = ''.join(c for c in mileage if c.isdigit())
                try:
                    mileage = int(mileage_nums) if mileage_nums else 0
                except ValueError:
                    mileage = 0  # Default value if conversion fails
                    
            # Clean and convert year to proper format
            year = vehicle['year']
            if isinstance(year, str):
                # Extract 4-digit year from string
                year_nums = ''.join(c for c in year if c.isdigit())
                try:
                    # Take first 4 digits or pad with zeros if shorter
                    year = int(year_nums[:4]) if year_nums else 0
                    # Validate year is reasonable (e.g., between 1900 and current year)
                    current_year = datetime.now().year
                    if year < 1900 or year > current_year:
                        year = 0
                except ValueError:
                    year = 0
                    
            # Clean and convert date to proper format
            date_str = vehicle['date']
            try:
                # Try parsing the date string to datetime object
                parsed_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                # If parsing fails, use current date as fallback
                parsed_date = datetime.now().strftime("%Y-%m-%d")
                    
            args = (
                scrape_date,
                vehicle['name'],
                vehicle['maker'],
                vehicle['model'],
                year,
                vehicle['location'],
                price,
                mileage,
                parsed_date,
                vehicle['image_url'],
                vehicle['listing_url']
            )
            cursor.callproc('InsertRiyasewanaScraper', args)
            
        connection.commit()
        print(f"Saved {len(vehicles)} vehicles to the database")
        
    except Exception as e:
        print(f"Error saving to database: {e}")
        print(f"Failed data: {args}")
        connection.rollback()
        
    finally:
        cursor.close()
        connection.close()
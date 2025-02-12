from pydantic import BaseModel

class Vehicle(BaseModel):
    name: str
    location: str
    price: float
    mileage: int
    date: str
    image_url: str
    listing_url: str

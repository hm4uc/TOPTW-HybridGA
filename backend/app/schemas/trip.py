from pydantic import BaseModel
from typing import List, Dict

# Input từ Mobile gửi lên
class UserPreferences(BaseModel):
    budget: float
    start_time: float  # Ví dụ 8.0 (8h sáng)
    end_time: float    # Ví dụ 17.0 (5h chiều)
    interests: Dict[str, float] # {"history": 1.5, "nature": 0.8}

# Output trả về cho Mobile
class PoiDetail(BaseModel):
    id: int
    name: str
    lat: float
    lon: float
    arrival_time: float
    leave_time: float
    price: float

class TripResponse(BaseModel):
    total_score: float
    total_cost: float
    total_time: float
    route: List[PoiDetail]
    execution_time: float
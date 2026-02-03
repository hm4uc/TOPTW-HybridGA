from pydantic import BaseModel
from typing import List, Dict

# Số sao (User chọn),Ý nghĩa ,      Trọng số W,     Tác động lên điểm POI
# ⭐,        Ghét / Không quan tâm,   0.1,       Điểm số bị chia 10 (Gần như không bao giờ được chọn vào lịch trình)
# ⭐⭐,      Ít quan tâm,             0.5,       Điểm số bị giảm một nửa
# ⭐⭐⭐,    Bình thường,             1.0,       Giữ nguyên điểm gốc (Base Score)
# ⭐⭐⭐⭐,  Thích,                   1.5,       Điểm số được cộng thêm 50%
# ⭐⭐⭐⭐⭐,Rất thích (Ưu tiên),     2.0,       Điểm số nhân đôi (Rất dễ được chọn)

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
from pydantic import BaseModel, Field
from typing import Dict, List, Optional


# Input from user
class UserPreferences(BaseModel):
    budget: float = Field(..., description="Ngân sách tối đa cho chuyến đi")
    start_time: float = Field(8.0, description="Thời gian bắt đầu chuyến đi (giờ)")
    end_time: float = Field(17.0, description="Thời gian kết thúc chuyến đi (giờ)")
    start_node_id: int = Field(..., description="ID điểm xuất phát (depot)")
    interests: Dict[str, float] = Field(..., description="Sở thích và trọng số tương ứng. "
                                                         "Key phải thuộc: history_culture, "
                                                         "nature_parks, food_drink, shopping, entertainment")

# Output
class ItineraryItem(BaseModel):
    order: int = Field(..., description="Thứ tự trong lộ trình")
    id: int = Field(..., description="ID điểm tham quan")
    name: str = Field(..., description="Tên điểm tham quan")
    category: Optional[str] = Field(None, description="Loại điểm tham quan")
    arrival: Optional[str] = Field(None, description="Thời gian đến (HH:MM)")
    wait: Optional[int] = Field(0, description="Thời gian chờ (phút)")
    start: Optional[str] = Field(None, description="Thời gian bắt đầu tham quan (HH:MM)")
    leave: Optional[str] = Field(None, description="Thời gian rời đi (HH:MM)")
    cost: float = Field(..., description="Chi phí tham quan")
    score: float = Field(..., description="Điểm đạt được tại điểm tham quan")

class OptimizationResponse(BaseModel):
    total_score: float = Field(..., description="Tổng điểm đạt được")
    total_cost: float = Field(..., description="Tổng chi phí")
    total_duration: float = Field(..., description="Tổng thời gian chuyến đi (giờ)")
    route: List[ItineraryItem] = Field(..., description="Lộ trình chi tiết")
    execution_time: float = Field(..., description="Thời gian chạy thuật toán (giây)")

from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Optional


# =============================================================================
#  Bảng ánh xạ: số sao người dùng chọn → trọng số dùng trong thuật toán
# =============================================================================
STAR_TO_WEIGHT: Dict[int, float] = {
    1: 0.1,   # Không quan tâm
    2: 0.5,   # Ít quan tâm
    3: 1.0,   # Trung bình (mức cơ sở)
    4: 1.5,   # Quan tâm nhiều
    5: 2.0,   # Rất quan tâm / ưu tiên cao nhất
}

# Danh sách category hợp lệ
VALID_CATEGORIES = {
    'history_culture', 'nature_parks', 'food_drink', 'shopping', 'entertainment'
}


# Input from user
class UserPreferences(BaseModel):
    budget: float = Field(..., description="Ngân sách tối đa cho chuyến đi")
    start_time: float = Field(8.0, description="Thời gian bắt đầu chuyến đi (giờ)")
    end_time: float = Field(17.0, description="Thời gian kết thúc chuyến đi (giờ)")
    start_node_id: int = Field(..., description="ID điểm xuất phát (depot)")
    interests: Dict[str, int] = Field(
        ...,
        description=(
            "Mức độ quan tâm của người dùng với từng loại hình địa điểm, "
            "tính bằng số sao từ 1 đến 5. "
            "Key phải thuộc: history_culture, nature_parks, food_drink, shopping, entertainment. "
            "1 sao = không quan tâm (w=0.1), 2 sao = ít quan tâm (w=0.5), "
            "3 sao = trung bình (w=1.0), 4 sao = quan tâm nhiều (w=1.5), "
            "5 sao = rất quan tâm (w=2.0)."
        )
    )

    @field_validator('interests')
    @classmethod
    def validate_interests(cls, v: Dict[str, int]) -> Dict[str, int]:
        """Kiểm tra key hợp lệ và giá trị nằm trong khoảng [1, 5]."""
        for category, stars in v.items():
            if category not in VALID_CATEGORIES:
                raise ValueError(
                    f"Category '{category}' không hợp lệ. "
                    f"Phải thuộc: {sorted(VALID_CATEGORIES)}"
                )
            if stars not in STAR_TO_WEIGHT:
                raise ValueError(
                    f"Số sao cho '{category}' phải là số nguyên từ 1 đến 5, "
                    f"nhận được: {stars}"
                )
        return v

    @property
    def interest_weights(self) -> Dict[str, float]:
        """
        Chuyển đổi số sao → trọng số float để thuật toán sử dụng.
        Category không được người dùng đánh giá sẽ có trọng số = 0.0.
        """
        return {cat: STAR_TO_WEIGHT[stars] for cat, stars in self.interests.items()}

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

"""
[DEPRECATED] schemas.py — Compatibility shim.

Các module mới nên import trực tiếp từ:
  • app.models.requests  → UserPreferences
  • app.models.responses → OptimizationResponse, ItineraryItem

File này chỉ re-export để tránh ImportError trong trường hợp còn code cũ
chưa được cập nhật. Sẽ xóa trong phiên bản tiếp theo.
"""

from app.models.requests import (   # noqa: F401
    UserPreferences,
    STAR_TO_WEIGHT,
    VALID_CATEGORIES,
    MIN_TOUR_DURATION_HOURS,
)
from app.models.responses import (  # noqa: F401
    ItineraryItem,
    OptimizationResponse,
)

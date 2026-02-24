from fastapi import APIRouter, HTTPException
from pydantic import ValidationError
import logging
from app.models.schemas import OptimizationResponse, UserPreferences
from app.services.algorithm.hga_engine import HybridGeneticAlgorithm
from app.services.data_loader import load_solomon_c101

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/optimize", response_model=OptimizationResponse)
async def optimize_itinerary(request: UserPreferences):
    """
    Endpoint tối ưu hóa lộ trình du lịch.

    Validation layers:
      1. Pydantic model validation (budget, thời gian, interests) → 422
      2. Business logic validation (start_node_id, khung giờ) → 400
      3. HGA execution → 500 nếu lỗi hệ thống
      4. Result validation (route rỗng) → 404
    """
    try:
        logger.info("Received optimization request with preferences: %s", request)

        # ── Edge Case 6: Validate start_node_id exists in dataset ─────────
        pois = load_solomon_c101()
        valid_ids = {p.id for p in pois}
        if request.start_node_id not in valid_ids:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Điểm xuất phát (start_node_id={request.start_node_id}) "
                    f"không tồn tại trong dataset. "
                    f"ID hợp lệ: 0 đến {max(valid_ids)}."
                ),
            )

        # ── Run HGA ───────────────────────────────────────────────────────
        hga_solver = HybridGeneticAlgorithm(request)
        result = hga_solver.run()

        # ── Edge Case 7: GA trả về route rỗng [Depot, Depot] ─────────────
        if not result:
            raise HTTPException(
                status_code=404,
                detail="Không tìm được lộ trình khả thi với các tùy chọn đã cho.",
            )

        # Kiểm tra route chỉ có Depot (không ghé được POI nào)
        if hasattr(result, 'route') and len(result.route) <= 2:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Không thể ghé thăm bất kỳ điểm nào trong khung thời gian "
                    f"và ngân sách đã cho ({request.start_time}h → {request.end_time}h, "
                    f"budget={request.budget:,.0f}). "
                    "Hãy thử mở rộng khung giờ hoặc tăng ngân sách."
                ),
            )

        return result

    except HTTPException:
        # Re-raise HTTPExceptions (đã có status code rõ ràng)
        raise

    except Exception as e:
        logger.error("Error during optimization: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Đã xảy ra lỗi trong quá trình tối ưu hóa lộ trình.",
        )
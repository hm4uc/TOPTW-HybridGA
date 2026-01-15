from fastapi import APIRouter
from app.schemas.trip import UserPreferences, TripResponse, PoiDetail
from app.services.data_loader import load_pois
from app.services.algorithm.ga_engine import GeneticAlgorithm
import time

router = APIRouter()
pois_db = load_pois() # Load dữ liệu khi khởi động

@router.post("/optimize", response_model=TripResponse)
async def optimize_trip(prefs: UserPreferences):
    start_time = time.time()

    # 1. Khởi tạo thuật toán
    ga = GeneticAlgorithm(pois_db, prefs)

    # 2. Chạy
    best_ind = ga.run()

    # 3. Format kết quả trả về
    execution_time = time.time() - start_time

    response_route = []
    # (Lưu ý: Logic tính giờ đến/đi chi tiết cần mapping lại từ hàm fitness)
    # Ở đây return dummy time cho các điểm để test flow
    curr_t = prefs.start_time
    for p in best_ind.route:
        response_route.append(PoiDetail(
            id=p.id, name=p.name, lat=p.lat, lon=p.lon,
            arrival_time=curr_t, leave_time=curr_t+1, price=p.price
        ))
        curr_t += 1.5

    return TripResponse(
        total_score=best_ind.total_score,
        total_cost=best_ind.total_cost,
        total_time=best_ind.total_time,
        route=response_route,
        execution_time=execution_time
    )
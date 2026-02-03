from fastapi import APIRouter, HTTPException
import logging
from app.models.schemas import OptimizationResponse, UserPreferences
from app.services.algorithm.hga_engine import HybridGeneticAlgorithm

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/optimize", response_model=OptimizationResponse)
async def optimize_itinerary(request: UserPreferences):
    try:
        logger.info("Received optimization request with preferences: %s", request)
        hga_solver = HybridGeneticAlgorithm(request)

        result = hga_solver.run()

        if not result:
            raise HTTPException(status_code=404, detail="No feasible itinerary found with the given preferences.")

        return result

    except Exception as e:
        logger.error("Error during optimization: %s", e)
        raise HTTPException(status_code=500, detail="An error occurred during itinerary optimization.")
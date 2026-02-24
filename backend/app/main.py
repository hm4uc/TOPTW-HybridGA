from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.models.schemas import OptimizationResponse, UserPreferences
from app.services.algorithm.hga_engine import HybridGeneticAlgorithm

app = FastAPI(title="TOPTW Hybrid GA API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix="/api")

@app.get("/")
def root():
    return {"status": "ok", "message": "Server is running..."}

@app.post("/optimize", response_model=OptimizationResponse)
async def optimize_itinerary(request: UserPreferences):
    solver = HybridGeneticAlgorithm(request)

    result = solver.run()
    return result
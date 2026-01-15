from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="TOPTW Hybrid GA API")

app.include_router(router, prefix="/api")

@app.get("/")
def root():
    return {"message": "Server is running..."}
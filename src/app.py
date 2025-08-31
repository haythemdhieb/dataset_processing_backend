from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from fastapi import FastAPI
from routes import dataset_routes
from config.settings import settings


app = FastAPI(
    title="CSV dataset processor",
    description="API REST for dataset processing",
    version="2.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dataset_routes.dataset_router, tags=["csv_dataset"], prefix="/datasets")

@app.get("/")
async def root():
    """root endpoint"""
    return {"message": "CSV Dataset API"}


if __name__ == '__main__':
    uvicorn.run(app, host=settings.HOST, port=int(settings.PORT))
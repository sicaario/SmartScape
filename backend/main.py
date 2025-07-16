from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routes.buy_mode import router as buy_router
from routes.sell_mode import router as sell_router
import config  # This will load the environment variables
import uvicorn

app = FastAPI(title="SmartScape", description="AI-powered Home Decor", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(buy_router)
app.include_router(sell_router)

@app.get("/")
async def root():
    return {"message": "SmartScape API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
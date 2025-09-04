from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field, ValidationError
from typing import Optional, List, Dict, Any
import asyncio
import logging
import time
import os

# Import services based on how we're running the server
try:
    # Try relative imports first (when running from root with uvicorn apis.main:app)
    from apis.weather_service import WeatherAPI
    from apis.carbon_service import CarbonFootprintCalculator
except ImportError:
    # Fallback to direct imports (when running from apis directory)
    from weather_service import WeatherAPI
    from carbon_service import CarbonFootprintCalculator

# Load environment variables
try:
    from dotenv import load_dotenv
    from pathlib import Path
    
    # Try to find .env file in parent directory
    BASE_DIR = Path(__file__).resolve().parent.parent
    dotenv_path = BASE_DIR / ".env"
    if dotenv_path.exists():
        load_dotenv(dotenv_path=dotenv_path)
    else:
        # Try current directory
        load_dotenv()
except ImportError:
    # If dotenv not available, just continue without it
    print("Warning: python-dotenv not installed. Environment variables won't be loaded from .env file")

# --- Security and Monitoring ---
API_KEY = os.getenv("API_GATEWAY_KEY", "test-key")
RATE_LIMIT = 60  # requests per minute per user
rate_limit_cache = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- FastAPI App ---
app = FastAPI(title="Sustainable Travel Planner API", version="1.0.0")

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} completed in {process_time:.2f}s")
    return response

@app.middleware("http")
async def rate_limiter(request: Request, call_next):
    user = request.headers.get("Authorization", "anonymous")
    now = int(time.time())
    window = now // 60
    key = f"{user}:{window}"
    count = rate_limit_cache.get(key, 0)
    if count >= RATE_LIMIT:
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
    rate_limit_cache[key] = count + 1
    return await call_next(request)

@app.middleware("http")
async def error_handler(request: Request, call_next):
    try:
        return await call_next(request)
    except ValidationError as ve:
        return JSONResponse(status_code=422, content={"detail": ve.errors()})
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

# --- Auth ---
auth_scheme = HTTPBearer()
def authenticate(credentials: HTTPAuthorizationCredentials = Depends(auth_scheme)):
    if credentials.credentials != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

# --- Pydantic Models ---
class WeatherRequest(BaseModel):
    location: str = Field(..., example="Berlin")

class WeatherResponse(BaseModel):
    description: str
    suitability: Optional[Dict[str, int]] = None
    alerts: Optional[str] = None

class CarbonRequest(BaseModel):
    trip: Dict[str, Any] = Field(..., example={"segments": [{"mode": "flight", "amount": 1200}]})

class CarbonResponse(BaseModel):
    total_emission: float
    breakdown: List[Dict[str, Any]]
    sustainability_score: str
    offset_kg: float
    offset_price: float
    recommendations: List[str]

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[str]] = None

class ChatResponse(BaseModel):
    answer: str
    sources: Optional[List[Dict[str, Any]]] = None

# --- Service Instances ---
try:
    weather_api = WeatherAPI()
    carbon_api = CarbonFootprintCalculator()
    logger.info("Services initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize services: {e}")
    # Create dummy services for testing
    weather_api = None
    carbon_api = None

# --- Endpoints ---
@app.post("/v1/weather", response_model=WeatherResponse, tags=["Weather"])
async def get_weather(req: WeatherRequest, auth: Any = Depends(authenticate)):
    if weather_api is None:
        return WeatherResponse(description="Weather service unavailable", suitability=None, alerts=None)
    
    try:
        weather = await asyncio.to_thread(weather_api.get_current_weather, req.location)
        suitability = {
            act: weather_api.suitability_score(weather, act)
            for act in ["hiking", "beach", "sightseeing"]
        }
        alerts = await asyncio.to_thread(weather_api.get_weather_alerts, req.location)
        desc = weather_api.format_weather_for_conversation(weather, req.location)
        alert_msg = weather_api.format_alerts_for_conversation(alerts, req.location)
        return WeatherResponse(description=desc, suitability=suitability, alerts=alert_msg)
    except Exception as e:
        logger.error(f"Weather API error: {e}")
        return WeatherResponse(description=f"Weather service error: {str(e)}", suitability=None, alerts=None)

@app.post("/v1/carbon-footprint", response_model=CarbonResponse, tags=["Carbon"])
async def get_carbon(req: CarbonRequest, auth: Any = Depends(authenticate)):
    if carbon_api is None:
        return CarbonResponse(
            total_emission=0.0,
            breakdown=[],
            sustainability_score="unknown",
            offset_kg=0.0,
            offset_price=0.0,
            recommendations=["Carbon service unavailable"]
        )
    
    try:
        result = await asyncio.to_thread(carbon_api.calculate_trip, req.trip)
        return CarbonResponse(**result)
    except Exception as e:
        logger.error(f"Carbon API error: {e}")
        return CarbonResponse(
            total_emission=0.0,
            breakdown=[],
            sustainability_score="error",
            offset_kg=0.0,
            offset_price=0.0,
            recommendations=[f"Carbon service error: {str(e)}"]
        )

@app.post("/v1/eco-recommendations", response_model=ChatResponse, tags=["Eco"])
async def eco_recommendations(req: ChatRequest, auth: Any = Depends(authenticate)):
    return ChatResponse(answer="Here are some eco-friendly travel tips: Use public transport, choose eco-friendly accommodations, pack light, and support local businesses.", sources=None)

@app.post("/v1/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(req: ChatRequest, auth: Any = Depends(authenticate)):
    return ChatResponse(answer="[RAG response here - integration pending]", sources=None)

@app.get("/v1/health", tags=["Health"])
async def health_check():
    try:
        weather_ok = weather_api is not None
        if weather_api:
            test_weather = await asyncio.to_thread(weather_api.get_current_weather, "Berlin")
            weather_ok = test_weather is not None
        carbon_ok = carbon_api is not None
        return {
            "weather": weather_ok, 
            "carbon": carbon_ok, 
            "status": "ok" if weather_ok and carbon_ok else "degraded"
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {"weather": False, "carbon": False, "status": "error", "error": str(e)}

# --- Root endpoint ---
@app.get("/")
async def root():
    return {"message": "Sustainable Travel Planner API", "docs": "/docs", "health": "/v1/health"}

# --- OpenAPI Customization ---
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Sustainable Travel Planner API",
        version="1.0.0",
        description="Unified API gateway for sustainable travel planning.",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# --- For running directly ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
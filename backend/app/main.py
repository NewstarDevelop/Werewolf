"""FastAPI application entry point."""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.api import api_router
from app.core.config import settings
from app.services.log_manager import init_game_logging

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Werewolf AI Game API",
    description="狼人杀 AI 游戏后端 API",
    version="1.0.0",
    debug=settings.DEBUG,
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)


@app.on_event("startup")
async def startup_event():
    """Log startup information and initialize services."""
    logger.info("Werewolf AI Game API starting up...")
    logger.info(f"LLM Model: {settings.LLM_MODEL}")
    logger.info(f"LLM Mock Mode: {settings.LLM_USE_MOCK}")
    if settings.OPENAI_API_KEY:
        logger.info("OpenAI API Key: configured")
    else:
        logger.warning("OpenAI API Key: NOT configured - using mock mode")

    # Initialize game logging
    init_game_logging()
    logger.info("Game logging initialized")


@app.get("/")
def root():
    """Root endpoint - health check."""
    return {
        "status": "ok",
        "message": "Werewolf AI Game API is running",
        "version": "1.0.0",
        "llm_mode": "mock" if settings.LLM_USE_MOCK or not settings.OPENAI_API_KEY else "real",
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

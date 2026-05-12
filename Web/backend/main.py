from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from database import init_db, close_connection
from routers import auth, users, admin, predict
from dotenv import load_dotenv
from contextlib import asynccontextmanager
import os

# Load environment variables
load_dotenv()

# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        init_db()
    except Exception as exc:
        print(f"Warning: database initialization skipped ({exc})")
    yield
    # Shutdown
    try:
        close_connection()
    except Exception:
        pass

# Initialize FastAPI app
app = FastAPI(
    title="Bot Hunter API",
    description="AI-powered bot detection and analysis platform API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend communication
# Defaults to localhost for local dev. Set CORS_ORIGINS env var for production.
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security scheme
security = HTTPBearer()

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(admin.router, tags=["Admin"])
app.include_router(predict.router, prefix="/api/predict", tags=["Prediction"])

@app.get("/")
async def root():
    return {
        "message": "Bot Hunter API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


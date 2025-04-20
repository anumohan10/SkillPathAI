from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sys
import os
import logging
from logging.config import dictConfig
import time

# Add parent directory to path to make relative imports work
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

app = FastAPI(
    title="SkillPathAI API",
    description="API for SkillPathAI Career Transition Platform",
    version="1.0.0"
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import all API routes
from backend.api.routes import auth, user_input, recommendations

# Include all routers
app.include_router(auth.router)
app.include_router(recommendations.router)
app.include_router(user_input.router)

logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request, call_next):
    start_time = time.time()
    
    # Log request details
    logger.debug(f"Request: {request.method} {request.url}")
    logger.debug(f"Headers: {request.headers}")
    
    # Try to log request body for POST/PUT
    if request.method in ["POST", "PUT"]:
        try:
            body = await request.body()
            logger.debug(f"Request body: {body.decode()}")
            # Reset the request body since we consumed it
            request._body = body
        except Exception as e:
            logger.error(f"Failed to log request body: {e}")
    
    # Process the request
    response = await call_next(request)
    
    # Log response details
    process_time = time.time() - start_time
    logger.debug(f"Response status: {response.status_code}")
    logger.debug(f"Response time: {process_time:.3f}s")
    
    return response

@app.get("/")
def read_root():
    return {"message": "Welcome to SkillPathAI API"}

# Define your logging configuration
logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(pathname)s:%(lineno)d - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "detailed",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": "api_server.log",
            "level": "DEBUG",
            "formatter": "detailed",
        },
    },
    "loggers": {
        "": {  # Root logger
            "handlers": ["console", "file"],
            "level": "DEBUG",
        },
        "uvicorn": {
            "handlers": ["console", "file"],
            "level": "INFO",
        },
        "uvicorn.error": {
            "handlers": ["console", "file"],
            "level": "INFO",
        },
    },
}

# Apply the configuration
dictConfig(logging_config)

# Enable detailed Snowflake connector logging
logging.getLogger('snowflake.connector').setLevel(logging.DEBUG)

if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True, log_level="debug") 
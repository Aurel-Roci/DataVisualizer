import uvicorn
import os
from fastapi import FastAPI

from .context_manager import lifespan
from .api.endpoints import router

from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    lifespan=lifespan,
    title="Blood Work Parser API",
    description="Upload and parse blood work PDF files",
    version="1.0.0"
)

app.include_router(router)


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000"))
    )
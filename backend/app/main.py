import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.endpoints import router
from .api.errors import register_error_handlers
from .context_manager import lifespan
from .core.config import get_settings
from .core.logging import setup_logging

settings = get_settings()
setup_logging(settings.log_level)

app = FastAPI(
    lifespan=lifespan,
    title="Blood Work Parser API",
    description="Upload and parse blood work PDF files",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # your Vue dev server
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
register_error_handlers(app)


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
    )

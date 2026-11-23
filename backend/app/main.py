from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .adapters.inbound.http.errors import register_error_handlers
from .adapters.inbound.http.routes import router
from .adapters.outbound.influx_repository import InfluxBloodworkRepository
from .adapters.outbound.pdf_camelot import CamelotReportExtractor
from .config.logging import setup_logging
from .config.settings import get_settings

settings = get_settings()
setup_logging(settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Composition root: build the concrete adapters once; routes only see ports and use cases"""
    repository = InfluxBloodworkRepository()
    app.state.repository = repository
    app.state.extractor = CamelotReportExtractor()
    yield
    repository.close()


app = FastAPI(
    lifespan=lifespan,
    title="Blood Work Parser API",
    description="Upload and parse blood work PDF files",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
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

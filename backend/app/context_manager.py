import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.datastructures import State

from .adapters.outbound.influx_repository import InfluxBloodworkRepository

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - create database service once
    logger.info("Starting up...")

    db_service = InfluxBloodworkRepository()
    app.state.db = db_service
    yield
    # Shutdown - clean up
    logger.info("Shutting down...")
    app.state.db.close()
    app.state = State()


def get_db(request: Request) -> InfluxBloodworkRepository:
    """Get database service from app state"""
    return request.app.state.db

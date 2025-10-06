from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.datastructures import State
from .services.database import InfluxDBService


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - create database service once
    print("Starting up...")

    db_service = InfluxDBService()
    app.state.db = db_service
    yield
    # Shutdown - clean up
    print("Shutting down...")
    app.state.db.close()
    app.state = State()


def get_db(request: Request) -> InfluxDBService:
    """Get database service from app state"""
    return request.app.state.db

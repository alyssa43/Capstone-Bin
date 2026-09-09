import asyncio
import logging

from config import FRONTEND_ORIGINS
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import bins, catch_all, websocket
from services.cleanup import sweep_loop

# Uvicorn only configures its own loggers, so without a root handler the
# retention sweep's INFO lines never reach the console.
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run the retention sweep in the background for the life of the app."""
    sweep_task = asyncio.create_task(sweep_loop())
    yield
    sweep_task.cancel()
    try:
        await sweep_task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="Request Bin", lifespan=lifespan)

frontend_origins = FRONTEND_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in frontend_origins.split(",") if origin.strip()],
    allow_methods=["*"],
    allow_headers=["Owner-Token"],
)

# bins must come first -- catch_all's /{full_path:path} would otherwise swallow it.
app.include_router(bins.router)
app.include_router(websocket.router)
app.include_router(catch_all.router)

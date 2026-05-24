

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.constants import EventType
from app.db.database import Base, engine

logger = logging.getLogger(__name__)



@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    - ON STARTUP : initialise logging, create DB tables.
    - ON SHUTDOWN: log shutdown event.
    """
    # Import here to avoid circular import at module level
    from app.core.logging_config import setup_logging
    from app.core.config import settings

    # Logging must be set up before anything else logs
    setup_logging(log_dir=settings.LOG_DIR, log_file=settings.LOG_FILE)

    logger.info(
        "Application starting up.",
        extra={"event_type": "startup", "app": settings.APP_NAME},
    )

    # Ensure log directory exists
    os.makedirs(settings.LOG_DIR, exist_ok=True)

    # Create all ORM-defined tables (idempotent)
    Base.metadata.create_all(bind=engine)
    logger.info(
        "Database tables initialised.",
        extra={"event_type": "startup", "detail": "tables ready"},
    )

    yield

    logger.info(
        "Application shutting down.",
        extra={"event_type": "shutdown"},
    )


def create_application() -> FastAPI:
    """Factory function that builds and configures the FastAPI app."""

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "AI-powered customer enquiry handling backend. "
            "Accepts inbound enquiries, matches them against SOPs, "
            "handles escalations, and schedules follow-ups."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    
    
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


    from app.api.enquiry_routes import router as enquiry_router

    app.include_router(enquiry_router, prefix="/enquiry", tags=["Enquiries"])

     
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(
            "Unhandled exception",
            extra={
                "event_type": EventType.API_ERROR,
                "path": request.url.path,
                "error": str(exc),
            },
        )
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "An unexpected error occurred.",
                "detail": str(exc),
            },
        )
    
    from fastapi.exceptions import RequestValidationError

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning(
            "Request validation failed.",
            extra={
                "event_type": EventType.API_ERROR.value,
                "path": request.url.path,
                "errors": exc.errors(),
            },
        )
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "message": "Request validation failed.",
                "detail": exc.errors(),
            },
        )

    from app.utils.exceptions import EnquiryNotFoundError

    @app.exception_handler(EnquiryNotFoundError)
    async def enquiry_not_found_handler(request: Request, exc: EnquiryNotFoundError):
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "message": str(exc),
                "detail": None,
            },
        )

    return app


app = create_application()


from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """
    Standard envelope for all API responses.

    Usage:
        return APIResponse(success=True, message="Done", data=some_schema)
    """
    success: bool = True
    message: str = "OK"
    data: Optional[T] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "message": "Enquiry created successfully.",
                "data": {},
            }
        }
    }


class ErrorResponse(BaseModel):
    """
    Standard error envelope — returned by exception handlers.
    """
    success: bool = False
    message: str
    detail: Optional[Any] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": False,
                "message": "Enquiry not found.",
                "detail": "No enquiry with id=99 exists.",
            }
        }
    }


class HealthResponse(BaseModel):
    """Returned by GET /health"""

    status: str
    database: str
    version: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "database": "connected",
                "version": "1.0.0",
            }
        }
    }
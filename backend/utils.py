"""Utility functions for the backend."""

from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import HTTPException


def error_response(code: str, message: str, details: Any = None) -> Dict[str, Any]:
    """Create an error response in the format specified in the plan.
    
    Returns: { "error": { "code": code, "message": message, "details": details } }
    """
    error_data = {"code": code, "message": message}
    if details is not None:
        error_data["details"] = details
    
    return {"error": error_data}


def raise_error_response(code: str, message: str, details: Any = None, status_code: int = 400) -> None:
    """Raise an HTTPException with the error envelope format."""
    error_data = error_response(code, message, details)
    raise HTTPException(status_code=status_code, detail=error_data)

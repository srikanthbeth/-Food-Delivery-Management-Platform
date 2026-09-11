from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from utils.exceptions import (
    BusinessRuleException,
    ResourceNotFoundException,
)


def business_rule_exception_handler(
    request: Request,
    exc: BusinessRuleException,
):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "message": str(exc),
        },
    )


def resource_not_found_exception_handler(
    request: Request,
    exc: ResourceNotFoundException,
):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "success": False,
            "message": str(exc),
        },
    )


def permission_exception_handler(
    request: Request,
    exc: PermissionError,
):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "success": False,
            "message": str(exc),
        },
    )


def value_error_handler(
    request: Request,
    exc: ValueError,
):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "message": str(exc),
        },
    )


def general_exception_handler(
    request: Request,
    exc: Exception,
):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "Internal server error",
        },
    )


def register_exception_handlers(app: FastAPI):
    app.add_exception_handler(
        BusinessRuleException,
        business_rule_exception_handler,
    )

    app.add_exception_handler(
        ResourceNotFoundException,
        resource_not_found_exception_handler,
    )

    app.add_exception_handler(
        PermissionError,
        permission_exception_handler,
    )

    app.add_exception_handler(
        ValueError,
        value_error_handler,
    )

    app.add_exception_handler(
        Exception,
        general_exception_handler,
    )
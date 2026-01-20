"""Middleware package"""
from app.middleware.request_logging import log_request_body_middleware

__all__ = ["log_request_body_middleware"]

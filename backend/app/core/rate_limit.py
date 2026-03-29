"""
Rate limiting middleware for FastAPI.
Simple in-memory rate limiter — sufficient for single-instance deployment.
For multi-instance, use Redis-based solution.
"""

import time
import logging
from collections import defaultdict
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple sliding window rate limiter.
    Limits requests per IP address.
    """

    def __init__(self, app, max_requests: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _clean_old(self, key: str, now: float):
        cutoff = now - self.window_seconds
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health check
        if request.url.path in ("/", "/api/health"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        self._clean_old(client_ip, now)

        if len(self._requests[client_ip]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later."
            )

        self._requests[client_ip].append(now)
        return await call_next(request)

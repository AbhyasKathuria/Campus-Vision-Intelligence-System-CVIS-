import time
from typing import Dict, Tuple
from fastapi import HTTPException, Request, status

class MemoryRateLimiter:
    def __init__(self):
        # key -> (tokens, last_refill_timestamp, max_tokens, refill_rate_per_sec)
        self.buckets: Dict[str, Tuple[float, float]] = {}

    def check_rate_limit(self, key: str, max_requests: int, window_seconds: int = 60) -> bool:
        now = time.time()
        fill_rate = max_requests / float(window_seconds)

        if key not in self.buckets:
            self.buckets[key] = (float(max_requests - 1), now)
            return True

        tokens, last_refill = self.buckets[key]
        # Refill tokens based on elapsed time
        elapsed = now - last_refill
        tokens = min(float(max_requests), tokens + elapsed * fill_rate)

        if tokens >= 1.0:
            self.buckets[key] = (tokens - 1.0, now)
            return True
        else:
            self.buckets[key] = (tokens, now)
            return False

rate_limiter = MemoryRateLimiter()

def enforce_rate_limit(request: Request, key_prefix: str, max_requests: int, window_seconds: int = 60):
    client_ip = request.client.host if request.client else "127.0.0.1"
    key = f"{key_prefix}:{client_ip}"
    if not rate_limiter.check_rate_limit(key, max_requests, window_seconds):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {max_requests} requests per {window_seconds}s."
        )

"""Basic single-process protection for the Gemini chat endpoint.

Production requires an explicit opt-in after external access controls
are configured. This limiter is not a substitute for gateway auth,
provider quotas, or shared distributed rate limiting.
"""

import os
import time
from collections import deque
from threading import Lock

from fastapi import HTTPException


class ChatRateLimiter:
    def __init__(self, per_client=8, global_limit=30, window_seconds=60):
        self.per_client = per_client
        self.global_limit = global_limit
        self.window_seconds = window_seconds
        self._by_client = {}
        self._all = deque()
        self._lock = Lock()

    def check(self, client_id, now=None):
        if now is None:
            now = time.monotonic()

        cutoff = now - self.window_seconds
        with self._lock:
            while self._all and self._all[0] <= cutoff:
                self._all.popleft()

            for key in list(self._by_client):
                events = self._by_client[key]
                while events and events[0] <= cutoff:
                    events.popleft()
                if not events:
                    del self._by_client[key]

            events = self._by_client.get(client_id)
            client_count = len(events) if events is not None else 0

            if client_count >= self.per_client or len(self._all) >= self.global_limit:
                oldest = (
                    events[0]
                    if client_count >= self.per_client
                    else self._all[0]
                )
                retry_after = max(1, int(oldest + self.window_seconds - now) + 1)
                raise HTTPException(
                    status_code=429,
                    detail="Chat request limit reached. Try again shortly.",
                    headers={"Retry-After": str(retry_after)},
                )

            if events is None:
                events = deque()
                self._by_client[client_id] = events
            events.append(now)
            self._all.append(now)


limiter = ChatRateLimiter()


def protect_chat_request(request):
    """Disable production chat by default and limit active requests."""
    environment = os.getenv("INSIGHTFORGE_ENV", "development").strip().lower()
    if environment == "production" and os.getenv(
        "INSIGHTFORGE_ENABLE_CHAT", "false"
    ).strip().lower() != "true":
        raise HTTPException(
            status_code=503,
            detail="AI chat is not enabled for this deployment.",
        )

    # Do not trust client-supplied X-Forwarded-For headers.
    client_id = request.client.host if request.client else "unknown"
    limiter.check(client_id)

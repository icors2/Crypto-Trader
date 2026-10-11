from __future__ import annotations

import logging

import httpx

log = logging.getLogger(__name__)


class Alerter:
    def __init__(self, topic: str | None, base_url: str = "https://ntfy.sh") -> None:
        self.topic = topic
        self.base_url = base_url.rstrip("/")

    def send(self, title: str, message: str, *, priority: str = "default") -> None:
        log.info("alert %s: %s", title, message)
        if not self.topic:
            return
        try:
            httpx.post(
                f"{self.base_url}/{self.topic}",
                content=message.encode("utf-8"),
                headers={"Title": title, "Priority": priority},
                timeout=8.0,
            )
        except httpx.HTTPError as exc:
            log.warning("alert failed: %s", exc)

from __future__ import annotations


class ScreenshotService:
    """Placeholder screenshot integration. Requires explicit configuration and authorized targets."""

    def capture(self, target: str) -> dict:
        return {
            "target": target,
            "status": "not_configured",
            "message": "Screenshot capture requires a configured gowitness or browser automation environment.",
        }

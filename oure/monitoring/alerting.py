import json
import logging
import urllib.request
from typing import Any

from oure.monitoring.watchlist import WatchlistAlert


class AlertDispatcher:
    def __init__(self, webhook_url: str | None = None) -> None:
        self.webhook_url = webhook_url
        self.logger = logging.getLogger("oure.alerting")

    def dispatch(self, alert: WatchlistAlert) -> None:
        if alert.alert_level == "ACTION":
            text = "OURE ALERT: ACTION REQUIRED"
        elif alert.alert_level == "MONITOR":
            text = "OURE ALERT: MONITOR REQUIRED"
        else:
            text = "OURE ALERT: NOMINAL"

        payload: dict[str, Any] = {
            "text": text,
            "asset": alert.asset_norad_id,
            "pc": alert.pc,
            "tca": alert.conjunction.tca.isoformat() + "Z",
            "miss_distance_km": alert.conjunction.miss_distance_km,
        }

        # Always log to structured JSON log via Python logging
        self.logger.info("Watchlist Alert Dispatched", extra={"payload": payload})

        if self.webhook_url:
            try:
                data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(
                    self.webhook_url,
                    data=data,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req) as response:
                    if response.status not in (200, 201, 204):
                        self.logger.error(
                            f"Failed to post to webhook: {response.status}"
                        )
            except Exception as e:
                self.logger.exception(f"Error posting alert to webhook: {e}")

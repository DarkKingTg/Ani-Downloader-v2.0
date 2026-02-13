from __future__ import annotations

import math
import time
from collections import deque
from typing import Deque, Dict, Optional


class AdvancedETACalculator:
    def __init__(self, window_size: int = 10) -> None:
        self.window_size = window_size
        self.speed_samples: Deque[float] = deque(maxlen=window_size)
        self.start_time: Optional[float] = None
        self.last_update_time: Optional[float] = None
        self.last_downloaded_units: float = 0.0
        self.total_units: float = 0.0

    def start(self, total_units: float) -> None:
        now = time.time()
        self.start_time = now
        self.last_update_time = now
        self.total_units = float(total_units)
        self.last_downloaded_units = 0.0
        self.speed_samples.clear()

    def update(self, downloaded_units: float) -> Dict[str, object]:
        now = time.time()
        if self.start_time is None or self.last_update_time is None:
            return self._result(downloaded_units, 0.0, None, None)

        dt = now - self.last_update_time
        du = float(downloaded_units) - self.last_downloaded_units

        if dt > 0 and du >= 0:
            speed = du / dt
            if speed > 0:
                self.speed_samples.append(speed)

        self.last_update_time = now
        self.last_downloaded_units = float(downloaded_units)

        avg_speed = sum(self.speed_samples) / len(self.speed_samples) if self.speed_samples else 0.0
        remaining = max(0.0, self.total_units - float(downloaded_units))
        eta_seconds = (remaining / avg_speed) if avg_speed > 0 else None
        elapsed = now - self.start_time

        return self._result(downloaded_units, avg_speed, eta_seconds, elapsed)

    def _result(
        self,
        downloaded_units: float,
        speed_units_per_s: float,
        eta_seconds: Optional[float],
        elapsed_seconds: Optional[float],
    ) -> Dict[str, object]:
        progress = (float(downloaded_units) / self.total_units * 100.0) if self.total_units > 0 else 0.0
        return {
            "downloaded_units": float(downloaded_units),
            "total_units": float(self.total_units),
            "speed_units_per_s": float(speed_units_per_s),
            "progress_percent": float(progress),
            "eta_seconds": eta_seconds,
            "eta_formatted": self._format_time(eta_seconds),
            "elapsed_seconds": elapsed_seconds,
            "elapsed_formatted": self._format_time(elapsed_seconds),
        }

    @staticmethod
    def _format_time(seconds: Optional[float]) -> str:
        if seconds is None or seconds <= 0 or math.isnan(seconds) or math.isinf(seconds):
            return "Calculating..."
        if seconds >= 3600:
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            return f"{h}h {m}m"
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m:02d}:{s:02d}"


def format_bytes(num_bytes: int) -> str:
    v = float(max(0, num_bytes))
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if v < 1024.0:
            return f"{v:.2f} {unit}"
        v /= 1024.0
    return f"{v:.2f} PB"


def format_speed(bps: float) -> str:
    if bps <= 0:
        return "0 B/s"
    return f"{format_bytes(int(bps))}/s"

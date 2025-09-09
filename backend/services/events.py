"""Telemetry event recorder."""

from __future__ import annotations

from typing import List, Dict

EVENTS: List[Dict] = []


def record(event: Dict) -> None:
    EVENTS.append(event)

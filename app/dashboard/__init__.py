"""Dashboard domain — re-exports bp and DashboardService (read-only, no model)."""
from __future__ import annotations

from app.dashboard.api import bp
from app.dashboard.services import DashboardService

__all__ = ["DashboardService", "bp"]

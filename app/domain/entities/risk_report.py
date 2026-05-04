"""Risk monitoring result entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class RiskReport:
    approved: bool
    risk_score: int
    risk_category: str
    blocked_items: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    unsupported_claims: list[str] = field(default_factory=list)
    safer_alternative: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "approved": self.approved,
            "risk_score": self.risk_score,
            "risk_category": self.risk_category,
            "blocked_items": self.blocked_items,
            "warnings": self.warnings,
            "unsupported_claims": self.unsupported_claims,
            "safer_alternative": self.safer_alternative,
            "metadata": self.metadata,
        }


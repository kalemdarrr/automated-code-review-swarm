"""RAG support checking for agent claims."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.utils.text_utils import keyword_overlap, normalize_whitespace


@dataclass(slots=True)
class HallucinationCheckResult:
    unsupported_claims: list[str] = field(default_factory=list)
    supported_claims: list[str] = field(default_factory=list)
    adjusted_confidence: float = 1.0


class HallucinationChecker:
    """Checks whether findings have rough textual support in RAG sources."""

    def __init__(self, support_threshold: float = 0.08) -> None:
        self.support_threshold = support_threshold

    def check_findings(
        self,
        findings: list[dict[str, Any]],
        rag_sources: list[dict[str, Any]],
        rag_confidence: float,
    ) -> HallucinationCheckResult:
        source_text = "\n".join(str(source.get("snippet", "")) for source in rag_sources)
        result = HallucinationCheckResult(adjusted_confidence=rag_confidence)
        if not findings:
            return result
        if not source_text.strip():
            result.unsupported_claims = [self._claim_text(finding) for finding in findings]
            result.adjusted_confidence = min(rag_confidence, 0.2)
            return result

        unsupported_count = 0
        for finding in findings:
            claim = self._claim_text(finding)
            overlap = keyword_overlap(claim, source_text)
            if overlap >= self.support_threshold:
                result.supported_claims.append(claim)
            else:
                unsupported_count += 1
                result.unsupported_claims.append(
                    f"{claim} Knowledge base confidence is low for this specific claim."
                )

        penalty = unsupported_count / max(len(findings), 1)
        result.adjusted_confidence = round(max(0.0, rag_confidence * (1.0 - 0.45 * penalty)), 4)
        return result

    @staticmethod
    def _claim_text(finding: dict[str, Any]) -> str:
        parts = [
            finding.get("title"),
            finding.get("vulnerability_name"),
            finding.get("owasp_category"),
            finding.get("explanation"),
            finding.get("suggested_fix"),
            finding.get("secure_fix"),
        ]
        return normalize_whitespace(" ".join(str(part) for part in parts if part))


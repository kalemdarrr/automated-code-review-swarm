"""Clean code and maintainability review agent."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from app.core.agents.base_agent import BaseAgent
from app.domain.entities.agent_finding import AgentFinding


class CodeReviewerAgent(BaseAgent):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            name="CodeReviewerAgent",
            role="Detect code smells, maintainability issues, performance problems, and SOLID violations.",
            system_prompt=(
                "You are a senior software engineer performing a professional code review. Use the RAG context "
                "for Clean Code, SOLID, Python, and performance guidance. Do not execute code."
            ),
            **kwargs,
        )

    def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        code = str(input_data.get("code", ""))
        language = str(input_data.get("language", "python"))
        rag_context = str(input_data.get("rag_context", ""))
        rag_sources = input_data.get("rag_sources", [])
        warnings: list[str] = []

        llm_findings: list[AgentFinding] = []
        llm_data, llm_warnings = self._run_llm_json(
            user_payload={"code": code, "language": language, "rag_context": rag_context},
            output_contract=(
                '{"findings": [{"title": str, "severity": "LOW|MEDIUM|HIGH", "explanation": str, '
                '"suggested_fix": str, "confidence_score": float, "why_it_matters": str}]}'
            ),
        )
        warnings.extend(llm_warnings)
        if llm_data:
            llm_findings = self._parse_llm_findings(llm_data)

        heuristic_findings = self._heuristic_scan(code)
        llm_findings = self._filter_low_signal_llm_findings(code, llm_findings)
        findings = self._merge_findings([*heuristic_findings, *llm_findings])
        self._attach_source_support(findings, rag_sources)

        return {
            "findings": [finding.as_dict() for finding in findings],
            "warnings": warnings,
            "used_heuristic_fallback": bool(warnings and self.settings.enable_heuristic_fallback),
        }

    def _parse_llm_findings(self, payload: dict[str, Any]) -> list[AgentFinding]:
        findings: list[AgentFinding] = []
        for item in payload.get("findings", []):
            if not isinstance(item, dict):
                continue
            findings.append(
                AgentFinding(
                    title=str(item.get("title", "Maintainability issue")),
                    severity=str(item.get("severity", "MEDIUM")).upper(),
                    explanation=str(item.get("explanation", "")),
                    suggested_fix=str(item.get("suggested_fix", "Refactor into smaller, testable units.")),
                    confidence_score=_clamp_confidence(item.get("confidence_score", 0.55)),
                    agent_name=self.name,
                    metadata={"source": "local_llm", "why_it_matters": item.get("why_it_matters", "")},
                )
            )
        return findings

    def _heuristic_scan(self, code: str) -> list[AgentFinding]:
        findings: list[AgentFinding] = []
        lines = code.splitlines()
        findings.extend(self._long_functions(lines))
        findings.extend(self._duplicated_lines(lines))
        for line_number, line in enumerate(lines, start=1):
            stripped = line.strip()
            lower = stripped.lower()
            if re.match(r"except\s*:", stripped):
                findings.append(
                    self._finding(
                        "Bare exception handler",
                        "MEDIUM",
                        "A bare except catches system-exiting exceptions and hides actionable failures.",
                        "Catch specific exception types and log or handle the failure path explicitly.",
                        line_number,
                        0.82,
                    )
                )
            if re.search(r"for\s+.+:", stripped) and self._loop_has_string_concat(lines, line_number):
                findings.append(
                    self._finding(
                        "Inefficient string concatenation in loop",
                        "LOW",
                        "Repeated concatenation inside loops can create unnecessary intermediate strings.",
                        "Accumulate values in a list and join once, or use an appropriate builder.",
                        line_number,
                        0.67,
                    )
                )
            if re.match(r"def\s+\w+\(.*=\s*(\[\]|\{\})", stripped):
                findings.append(
                    self._finding(
                        "Mutable default argument",
                        "MEDIUM",
                        "Mutable defaults are shared between function calls and can leak state.",
                        "Use None as the default and create a new list or dict inside the function.",
                        line_number,
                        0.86,
                    )
                )
            if "todo" in lower or "fixme" in lower:
                findings.append(
                    self._finding(
                        "Unresolved implementation marker",
                        "LOW",
                        "TODO/FIXME markers in critical paths reduce report readiness and maintainability.",
                        "Convert the marker into tracked work or complete the implementation before release.",
                        line_number,
                        0.6,
                    )
                )
        if self._missing_input_validation(code):
            findings.append(
                AgentFinding(
                    title="Missing input validation",
                    severity="HIGH",
                    explanation="User-controlled inputs appear to flow into database, file, or expression operations without validation.",
                    suggested_fix="Validate type, length, format, and allowed values at the boundary before using inputs.",
                    confidence_score=0.77,
                    agent_name=self.name,
                    metadata={
                        "source": "static_heuristic",
                        "why_it_matters": "Validation reduces exploitability and makes downstream code simpler.",
                    },
                )
            )
        if self._mixed_responsibilities(code):
            findings.append(
                AgentFinding(
                    title="Mixed responsibilities in function",
                    severity="LOW",
                    explanation="A function appears to combine persistence, expression evaluation, file access, subprocess work, and response formatting.",
                    suggested_fix="Split the workflow into validation, data access, computation, file access, and response assembly functions.",
                    confidence_score=0.72,
                    agent_name=self.name,
                    metadata={
                        "source": "static_heuristic",
                        "why_it_matters": "Single-purpose units are easier to secure, test, and modify independently.",
                    },
                )
            )
        return findings

    def _long_functions(self, lines: list[str]) -> list[AgentFinding]:
        findings: list[AgentFinding] = []
        function_start: int | None = None
        function_name = ""
        for index, line in enumerate([*lines, "def __sentinel__(): pass"], start=1):
            match = re.match(r"\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", line)
            if match:
                if function_start is not None:
                    length = index - function_start
                    if length > 35:
                        findings.append(
                            AgentFinding(
                                title=f"Long function: {function_name}",
                                severity="MEDIUM",
                                explanation=f"Function spans about {length} lines, which makes review and testing harder.",
                                suggested_fix="Extract validation, data access, and formatting into focused functions.",
                                confidence_score=0.74,
                                agent_name=self.name,
                                metadata={
                                    "source": "static_heuristic",
                                    "line": function_start,
                                    "why_it_matters": "Small cohesive functions are easier to test and reason about.",
                                },
                            )
                        )
                function_start = index
                function_name = match.group(1)
        return findings

    def _duplicated_lines(self, lines: list[str]) -> list[AgentFinding]:
        normalized = [line.strip() for line in lines if len(line.strip()) > 18 and not line.strip().startswith("#")]
        duplicates = [line for line, count in Counter(normalized).items() if count >= 3 and _is_duplication_signal(line)]
        if not duplicates:
            return []
        return [
            AgentFinding(
                title="Duplicated code",
                severity="LOW",
                explanation="Repeated code fragments increase maintenance cost and bug-fix drift.",
                suggested_fix="Extract repeated logic into a named helper or shared validation function.",
                confidence_score=0.68,
                agent_name=self.name,
                evidence=duplicates[0],
                metadata={
                    "source": "static_heuristic",
                    "why_it_matters": "Duplication makes future fixes easy to apply inconsistently.",
                },
            )
        ]

    @staticmethod
    def _loop_has_string_concat(lines: list[str], line_number: int) -> bool:
        window = lines[line_number : min(len(lines), line_number + 6)]
        return any("+=" in line and ("\"" in line or "'" in line) for line in window)

    @staticmethod
    def _missing_input_validation(code: str) -> bool:
        lower = code.lower()
        has_user_input = any(token in lower for token in ("request.", "input(", "filename", "user_id", "expr", "payload"))
        risky_sink = any(token in lower for token in ("execute(", "eval(", "open(", "subprocess", "os.system"))
        validation = any(token in lower for token in ("validate", "isinstance", "match(", "fullmatch", "allowed", "raise valueerror"))
        return has_user_input and risky_sink and not validation

    @staticmethod
    def _mixed_responsibilities(code: str) -> bool:
        lower = code.lower()
        concerns = [
            any(token in lower for token in ("execute(", "select ", "insert ", "update ")),
            "eval(" in lower,
            "open(" in lower,
            "shell=true" in lower or "os.system" in lower,
            "pickle.loads" in lower or "yaml.load" in lower,
        ]
        return sum(1 for concern in concerns if concern) >= 3

    @staticmethod
    def _filter_low_signal_llm_findings(code: str, findings: list[AgentFinding]) -> list[AgentFinding]:
        lowered = code.lower()
        accepted: list[AgentFinding] = []
        for finding in findings:
            title = finding.title.lower()
            explanation = finding.explanation.lower()
            if finding.confidence_score < 0.58:
                continue
            if title in {"sql execution", "sql injection risk", "unsafe eval execution"}:
                continue
            if "sql" in title and "select" not in lowered and "execute(" not in lowered:
                continue
            if "injection" in title and "eval(" not in lowered and "execute(" not in lowered and "shell=true" not in lowered:
                continue
            if "subprocess" in title and "subprocess" not in lowered and "os.system" not in lowered:
                continue
            if "path traversal" in title and "filename" not in lowered and "open(" not in lowered:
                continue
            if "security" in explanation and all(token not in lowered for token in ("execute(", "eval(", "subprocess", "open(")):
                continue
            accepted.append(finding)
        return accepted

    def _finding(
        self,
        title: str,
        severity: str,
        explanation: str,
        fix: str,
        line_number: int,
        confidence: float,
    ) -> AgentFinding:
        return AgentFinding(
            title=title,
            severity=severity,
            explanation=f"{explanation} Detected near line {line_number}.",
            suggested_fix=fix,
            confidence_score=confidence,
            agent_name=self.name,
            metadata={
                "source": "static_heuristic",
                "line": line_number,
                "why_it_matters": explanation,
            },
        )

    @staticmethod
    def _merge_findings(findings: list[AgentFinding]) -> list[AgentFinding]:
        merged: dict[str, AgentFinding] = {}
        for finding in findings:
            key = finding.title.lower()
            existing = merged.get(key)
            if existing is None or finding.confidence_score > existing.confidence_score:
                merged[key] = finding
        return sorted(merged.values(), key=lambda item: _severity_rank(item.severity), reverse=True)

    @staticmethod
    def _attach_source_support(findings: list[AgentFinding], rag_sources: list[dict[str, Any]]) -> None:
        for finding in findings:
            supports: list[str] = []
            for source in rag_sources:
                category = str(source.get("category", "")).lower()
                snippet = str(source.get("snippet", ""))
                if category in {"clean_code", "python_docs", "pytorch_docs"} or finding.title.lower().split()[0] in snippet.lower():
                    supports.append(f"{source.get('source', 'unknown')} ({source.get('relevance_score', 0)})")
            finding.source_support = supports[:3]


def _clamp_confidence(value: Any) -> float:
    try:
        return round(max(0.0, min(1.0, float(value))), 2)
    except (TypeError, ValueError):
        return 0.55


def _severity_rank(severity: str) -> int:
    return {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0}.get(severity.upper(), 1)


def _is_duplication_signal(line: str) -> bool:
    lowered = line.lower()
    noise_prefixes = ("class ", "def ", "return ", "raise ", "from ", "import ")
    if lowered.startswith(noise_prefixes):
        return False
    return any(token in line for token in ("(", ")", "=", "[", "]", "{", "}"))

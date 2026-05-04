"""Security auditor agent."""

from __future__ import annotations

import re
from typing import Any

from app.core.agents.base_agent import BaseAgent
from app.domain.entities.vulnerability import Vulnerability


class SecurityAuditorAgent(BaseAgent):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            name="SecurityAuditorAgent",
            role="Detect security vulnerabilities and unsafe remediation suggestions.",
            system_prompt=(
                "You are a senior application security auditor. Use the supplied RAG context, OWASP references, "
                "and code text to identify vulnerabilities. Do not execute code. Mark uncertainty clearly."
            ),
            **kwargs,
        )

    def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        code = str(input_data.get("code", ""))
        language = str(input_data.get("language", "python"))
        rag_context = str(input_data.get("rag_context", ""))
        rag_sources = input_data.get("rag_sources", [])
        warnings: list[str] = []

        llm_findings: list[Vulnerability] = []
        llm_data, llm_warnings = self._run_llm_json(
            user_payload={"code": code, "language": language, "rag_context": rag_context},
            output_contract=(
                '{"findings": [{"vulnerability_name": str, "owasp_category": str|null, '
                '"severity": "LOW|MEDIUM|HIGH|CRITICAL", "vulnerable_code": str, '
                '"explanation": str, "secure_fix": str, "confidence_score": float}]}'
            ),
        )
        warnings.extend(llm_warnings)
        if llm_data:
            llm_findings = self._parse_llm_findings(llm_data)

        heuristic_findings = self._heuristic_scan(code)
        findings = self._merge_findings([*heuristic_findings, *llm_findings])
        self._attach_source_support(findings, rag_sources)

        return {
            "findings": [finding.as_dict() for finding in findings],
            "warnings": warnings,
            "used_heuristic_fallback": bool(warnings and self.settings.enable_heuristic_fallback),
        }

    def _parse_llm_findings(self, payload: dict[str, Any]) -> list[Vulnerability]:
        findings: list[Vulnerability] = []
        for item in payload.get("findings", []):
            if not isinstance(item, dict):
                continue
            findings.append(
                Vulnerability(
                    vulnerability_name=str(item.get("vulnerability_name", "Potential vulnerability")),
                    owasp_category=item.get("owasp_category"),
                    severity=str(item.get("severity", "MEDIUM")).upper(),
                    vulnerable_code=item.get("vulnerable_code"),
                    explanation=str(item.get("explanation", "")),
                    secure_fix=str(item.get("secure_fix", "Validate input and use safe APIs.")),
                    confidence_score=_clamp_confidence(item.get("confidence_score", 0.55)),
                    metadata={"source": "local_llm"},
                )
            )
        return findings

    def _heuristic_scan(self, code: str) -> list[Vulnerability]:
        findings: list[Vulnerability] = []
        lines = code.splitlines()
        tainted_sql_vars: set[str] = set()
        for line_number, line in enumerate(lines, start=1):
            stripped = line.strip()
            lower = stripped.lower()
            if re.search(
                r"(?i)\b[A-Za-z0-9_]*(password|passwd|secret|api_key|token)[A-Za-z0-9_]*\s*=\s*['\"][^'\"]{4,}['\"]",
                stripped,
            ):
                findings.append(
                    self._finding(
                        "Hardcoded secret",
                        "HIGH",
                        "A credential-like value is embedded directly in source code.",
                        "Load secrets from environment variables or a managed secret store and rotate exposed values.",
                        stripped,
                        line_number,
                        "OWASP A07: Identification and Authentication Failures",
                        0.86,
                    )
                )
            assignment = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)", stripped)
            if assignment and _looks_like_unsafe_sql(assignment.group(2)):
                tainted_sql_vars.add(assignment.group(1))
                findings.append(
                    self._finding(
                        "SQL injection risk",
                        "CRITICAL",
                        "SQL appears to be constructed with string interpolation or concatenation before execution.",
                        "Use parameterized queries or an ORM query builder with bound parameters.",
                        stripped,
                        line_number,
                        "OWASP A03: Injection",
                        0.9,
                    )
                )
            if "execute(" in lower and ("select" in lower or "insert" in lower or "update" in lower):
                if any(marker in stripped for marker in ("f\"", "f'", "%", ".format(", "+")):
                    findings.append(
                        self._finding(
                            "SQL injection risk",
                            "CRITICAL",
                            "SQL appears to be constructed with string interpolation or concatenation.",
                            "Use parameterized queries or an ORM query builder with bound parameters.",
                            stripped,
                            line_number,
                            "OWASP A03: Injection",
                            0.9,
                        )
                    )
            if "execute(" in lower and any(re.search(rf"\b{re.escape(var)}\b", stripped) for var in tainted_sql_vars):
                findings.append(
                    self._finding(
                        "SQL injection risk",
                        "CRITICAL",
                        "A previously interpolated SQL string is passed into execute.",
                        "Pass SQL text with placeholders and provide user values as bound parameters.",
                        stripped,
                        line_number,
                        "OWASP A03: Injection",
                        0.88,
                    )
                )
            if re.search(r"\beval\s*\(", stripped):
                findings.append(
                    self._finding(
                        "Unsafe eval execution",
                        "CRITICAL",
                        "eval executes attacker-controlled text as code when input is not strictly controlled.",
                        "Replace eval with a constrained parser, allowlist, or ast.literal_eval for simple literals.",
                        stripped,
                        line_number,
                        "OWASP A03: Injection",
                        0.91,
                    )
                )
            if "shell=true" in lower or re.search(r"\bos\.system\s*\(", stripped):
                findings.append(
                    self._finding(
                        "Insecure subprocess usage",
                        "HIGH",
                        "Shell execution can allow command injection when arguments include user-controlled data.",
                        "Use subprocess.run with a list of arguments, shell=False, and strict allowlists.",
                        stripped,
                        line_number,
                        "OWASP A03: Injection",
                        0.86,
                    )
                )
            if _looks_like_user_controlled_path_access(stripped):
                findings.append(
                    self._finding(
                        "Path traversal risk",
                        "HIGH",
                        "File paths appear to include user-controlled input without normalization or base-directory checks.",
                        "Normalize the path, resolve it against an allowlisted base directory, and reject traversal outside it.",
                        stripped,
                        line_number,
                        "OWASP A01: Broken Access Control",
                        0.82,
                    )
                )
            if "pickle.loads" in lower or ("yaml.load" in lower and "safeloader" not in lower):
                findings.append(
                    self._finding(
                        "Unsafe deserialization",
                        "HIGH",
                        "Unsafe deserialization can instantiate unexpected objects or execute gadget chains.",
                        "Use safe loaders, signed data, schema validation, or safer serialization formats.",
                        stripped,
                        line_number,
                        "OWASP A08: Software and Data Integrity Failures",
                        0.83,
                    )
                )
        return findings

    def _finding(
        self,
        name: str,
        severity: str,
        explanation: str,
        fix: str,
        evidence: str,
        line_number: int,
        owasp: str,
        confidence: float,
    ) -> Vulnerability:
        return Vulnerability(
            vulnerability_name=name,
            owasp_category=owasp,
            severity=severity,
            vulnerable_code=evidence,
            explanation=f"{explanation} Detected near line {line_number}.",
            secure_fix=fix,
            confidence_score=confidence,
            metadata={"source": "static_heuristic", "line": line_number},
        )

    @staticmethod
    def _merge_findings(findings: list[Vulnerability]) -> list[Vulnerability]:
        merged: dict[str, Vulnerability] = {}
        for finding in findings:
            key = finding.vulnerability_name.lower()
            existing = merged.get(key)
            if existing is None:
                merged[key] = finding
                continue
            if finding.vulnerable_code and finding.vulnerable_code not in str(existing.vulnerable_code):
                existing.vulnerable_code = f"{existing.vulnerable_code or ''}\n{finding.vulnerable_code}".strip()
            if finding.confidence_score > existing.confidence_score:
                existing.confidence_score = finding.confidence_score
                existing.explanation = finding.explanation
                existing.secure_fix = finding.secure_fix
            if _severity_rank(finding.severity) > _severity_rank(existing.severity):
                existing.severity = finding.severity
        return sorted(merged.values(), key=lambda item: _severity_rank(item.severity), reverse=True)

    @staticmethod
    def _attach_source_support(findings: list[Vulnerability], rag_sources: list[dict[str, Any]]) -> None:
        for finding in findings:
            supports: list[str] = []
            for source in rag_sources:
                category = str(source.get("category", "")).lower()
                snippet = str(source.get("snippet", ""))
                if "owasp" in category or "secure" in category or finding.vulnerability_name.lower().split()[0] in snippet.lower():
                    supports.append(f"{source.get('source', 'unknown')} ({source.get('relevance_score', 0)})")
            finding.source_support = supports[:3]


def _clamp_confidence(value: Any) -> float:
    try:
        return round(max(0.0, min(1.0, float(value))), 2)
    except (TypeError, ValueError):
        return 0.55


def _severity_rank(severity: str) -> int:
    return {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0}.get(severity.upper(), 1)


def _looks_like_unsafe_sql(expression: str) -> bool:
    lower = expression.lower()
    has_sql = any(keyword in lower for keyword in ("select ", "insert ", "update ", "delete "))
    has_interpolation = any(marker in expression for marker in ("f\"", "f'", "{", "%", ".format(", "+"))
    return has_sql and has_interpolation


def _looks_like_user_controlled_path_access(line: str) -> bool:
    normalized = line.lower()
    if not re.search(r"\b(open|send_file|read_text)\s*\(", normalized):
        return False

    # Require strong user-input indicators; avoid generic variables like `path`.
    user_markers = (
        "filename",
        "file_name",
        "request.",
        "request[",
        "request.get",
        "input(",
        "user_input",
        "payload",
    )
    if not any(marker in normalized for marker in user_markers):
        return False

    # Also require dynamic path construction or direct variable flow.
    dynamic_markers = ("+", "f\"", "f'", ".format(", "join(")
    return any(marker in line for marker in dynamic_markers) or "open(" in normalized

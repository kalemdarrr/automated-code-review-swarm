"""Dangerous command and unsafe remediation detection."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(slots=True)
class CommandSafetyResult:
    dangerous_commands: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def safe(self) -> bool:
        return not self.dangerous_commands


class CommandSafetyFilter:
    """Detects destructive or high-risk terminal command suggestions."""

    def __init__(self) -> None:
        self.patterns: list[tuple[re.Pattern[str], str]] = [
            (re.compile(r"\brm\s+-rf\s+[/~$*]?", re.IGNORECASE), "Destructive recursive delete command"),
            (re.compile(r"\bcurl\b.+\|\s*(?:sh|bash|zsh)\b", re.IGNORECASE), "Piped remote script execution"),
            (re.compile(r"\bwget\b.+\|\s*(?:sh|bash|zsh)\b", re.IGNORECASE), "Piped remote script execution"),
            (re.compile(r"\bchmod\s+777\b", re.IGNORECASE), "Overly permissive chmod"),
            (re.compile(r"\bsudo\s+", re.IGNORECASE), "Privileged sudo command"),
            (re.compile(r"\bDROP\s+DATABASE\b", re.IGNORECASE), "Destructive database command"),
            (re.compile(r"\bTRUNCATE\s+TABLE\b", re.IGNORECASE), "Destructive database command"),
            (re.compile(r"\b(?:cat|type)\s+.*(?:id_rsa|\.env|credentials|token)", re.IGNORECASE), "Credential exposure"),
            (re.compile(r"\b(?:nc|netcat)\b.+\b(?:-e|--exec)\b", re.IGNORECASE), "Shell exfiltration pattern"),
        ]

    def scan(self, text: str) -> CommandSafetyResult:
        result = CommandSafetyResult()
        for pattern, label in self.patterns:
            for match in pattern.finditer(text):
                result.dangerous_commands.append(match.group(0))
                result.warnings.append(label)
        return result


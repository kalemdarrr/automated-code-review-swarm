# Secure Coding Guidelines

Treat submitted code as text during review. Never execute uploaded code or shell commands extracted from user input.

Validate inputs at trust boundaries. Check type, length, range, format, and allowlisted values before using input in database queries, file paths, subprocess arguments, or expression parsers.

For safe file access, resolve the requested path against an allowlisted base directory and reject paths that escape the base directory after normalization.

For subprocess calls, pass arguments as a list, keep `shell=False`, and allowlist executable names and arguments. Avoid suggesting destructive commands such as recursive delete, privileged sudo operations, or piped remote scripts.

For secrets, use environment variables, a vault, or cloud secret manager. If a secret was committed, rotate it and remove it from history according to the organization's incident process.


# OWASP Top 10 Review Notes

OWASP A01 Broken Access Control includes failures that allow users to access files, records, or functions outside their authorization boundary. Path traversal occurs when untrusted path input is joined with a server-side directory without normalization and base-directory enforcement.

OWASP A03 Injection includes SQL injection, command injection, and expression-language injection. SQL queries should use parameterized statements with bound variables instead of string concatenation, format strings, or interpolation. Shell commands should avoid `shell=True` with user-controlled arguments.

OWASP A07 Identification and Authentication Failures includes poor credential handling. Passwords, tokens, API keys, and database secrets should not be hardcoded in source code. Use environment variables or a managed secret store and rotate exposed credentials.

OWASP A08 Software and Data Integrity Failures includes unsafe deserialization and trust of unverified data. Use safe parsers, schema validation, and signed artifacts for sensitive inputs.


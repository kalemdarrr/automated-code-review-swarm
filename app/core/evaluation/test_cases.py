"""Built-in benchmark cases for extrinsic evaluation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BenchmarkCase:
    case_id: str
    language: str
    code: str
    expected_vulnerability: str | None
    expected_severity: str
    expected_clean_code_issue: str | None


def built_in_cases() -> list[BenchmarkCase]:
    return [
        BenchmarkCase(
            case_id="sql_injection",
            language="python",
            code="""
def get_user(conn, user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return conn.execute(query).fetchone()
""",
            expected_vulnerability="SQL injection",
            expected_severity="CRITICAL",
            expected_clean_code_issue="Missing input validation",
        ),
        BenchmarkCase(
            case_id="hardcoded_password",
            language="python",
            code="""
def connect():
    password = "super-secret-prod-password"
    return login("admin", password)
""",
            expected_vulnerability="Hardcoded secret",
            expected_severity="HIGH",
            expected_clean_code_issue=None,
        ),
        BenchmarkCase(
            case_id="unsafe_eval",
            language="python",
            code="""
def calculate(expr):
    return eval(expr)
""",
            expected_vulnerability="Unsafe eval",
            expected_severity="CRITICAL",
            expected_clean_code_issue="Missing input validation",
        ),
        BenchmarkCase(
            case_id="path_traversal",
            language="python",
            code="""
def read_profile(filename):
    return open("/srv/profiles/" + filename).read()
""",
            expected_vulnerability="Path traversal",
            expected_severity="HIGH",
            expected_clean_code_issue="Missing input validation",
        ),
        BenchmarkCase(
            case_id="insecure_subprocess",
            language="python",
            code="""
import subprocess

def ping(host):
    return subprocess.check_output("ping -c 1 " + host, shell=True)
""",
            expected_vulnerability="Insecure subprocess",
            expected_severity="HIGH",
            expected_clean_code_issue="Missing input validation",
        ),
        BenchmarkCase(
            case_id="bad_exception_handling",
            language="python",
            code="""
def parse_int(value):
    try:
        return int(value)
    except:
        return None
""",
            expected_vulnerability=None,
            expected_severity="MEDIUM",
            expected_clean_code_issue="Bare exception",
        ),
        BenchmarkCase(
            case_id="duplicated_code",
            language="python",
            code="""
def normalize_a(value):
    value = value.strip().lower()
    return value.replace(" ", "_")

def normalize_b(value):
    value = value.strip().lower()
    return value.replace(" ", "_")
""",
            expected_vulnerability=None,
            expected_severity="LOW",
            expected_clean_code_issue="Duplicated code",
        ),
        BenchmarkCase(
            case_id="long_function",
            language="python",
            code="""
def process(items):
    total = 0
""" + "\n".join(f"    total += item.get('v{i}', 0)" for i in range(40)) + """
    return total
""",
            expected_vulnerability=None,
            expected_severity="MEDIUM",
            expected_clean_code_issue="Long function",
        ),
        BenchmarkCase(
            case_id="missing_input_validation",
            language="python",
            code="""
def update_email(conn, user_id, email):
    return conn.execute(f"UPDATE users SET email='{email}' WHERE id={user_id}")
""",
            expected_vulnerability="SQL injection",
            expected_severity="CRITICAL",
            expected_clean_code_issue="Missing input validation",
        ),
        BenchmarkCase(
            case_id="inefficient_loop",
            language="python",
            code="""
def render(items):
    output = ""
    for item in items:
        output += "<li>" + item + "</li>"
    return output
""",
            expected_vulnerability=None,
            expected_severity="LOW",
            expected_clean_code_issue="Inefficient string concatenation",
        ),
    ]


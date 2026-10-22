#!/usr/bin/env python3
"""Offline heuristics to detect common credential patterns before public commits.

Results show only filenames, line numbers, and categories, never secret values.
False negatives are possible; also use GitHub secret scanning / push protection.
"""
from pathlib import Path
import re

EXTENSIONS = {".py", ".json", ".md", ".txt", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".svg", ".html", ".sh", ".ps1"}
SKIP = {".git", ".venv", "venv", "node_modules", "__pycache__", "dist", "build", ".pytest_cache"}
PATTERNS = {
    "OpenAI API key": re.compile(r"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{15,}\b"),
    "GitHub token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{25,})\b"),
    "AWS access key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "Google API key": re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b"),
    "Stripe secret": re.compile(r"\b(?:sk_live|rk_live)_[A-Za-z0-9]{16,}\b"),
    "Slack token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{12,}\b"),
    "Private key block": re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"),
    "Known webhook URL": re.compile(r"https?://(?:discord(?:app)?\.com/api/webhooks|hooks\.slack\.com/services)/[^\s<>\"']+"),
    "Basic-Auth URL": re.compile(r"https?://[^/\s:@\"']+:[^/\s@\"']+@[^\s\"'<>]+"),
    "Hardcoded bearer": re.compile(r"\bBearer\s+[A-Za-z0-9_.-]{28,}\b"),
}
SENSITIVE_NAMES = {".env", ".netrc", ".npmrc", ".pypirc", "credentials.json", "secrets.json"}
SENSITIVE_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".secret"}

def main():
    findings = []
    for path in Path(".").rglob("*"):
        if not path.is_file() or any(part in SKIP for part in path.parts):
            continue
        if path.name in SENSITIVE_NAMES or (path.name.startswith(".env.") and path.name != ".env.example") or path.suffix in SENSITIVE_SUFFIXES:
            findings.append((str(path), 0, "sensitive filename"))
            continue
        if path.suffix.lower() not in EXTENSIONS:
            continue
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for label, regex in PATTERNS.items():
            for match in regex.finditer(source):
                findings.append((str(path), source.count("\n", 0, match.start()) + 1, label))
    for filename, line, label in findings:
        print(f"BLOCKED {filename}:{line}: {label}")
    if findings:
        return 1
    print("PASS: no common secret patterns found. This is a heuristic check, not a guarantee.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

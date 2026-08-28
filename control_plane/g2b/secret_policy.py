"""Content-only secret policy shared by repository and installed boundaries."""
from __future__ import annotations

import hashlib
import re
from collections.abc import Iterator


CONTENT_RULES = {
    "private-key-material": re.compile(
        rb"-----BEGIN (?:(?:OPENSSH|RSA|EC|DSA|ENCRYPTED) )?PRIVATE KEY-----"
    ),
    "pgp-private-key-material": re.compile(
        rb"-----BEGIN PGP PRIVATE " rb"KEY BLOCK-----"
    ),
    "age-secret-key": re.compile(rb"\bAGE-SECRET-KEY-1[0-9A-Z]{20,}\b"),
    "aws-access-key": re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "github-token": re.compile(rb"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    "github-fine-grained-token": re.compile(rb"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    "gitlab-token": re.compile(rb"\bglpat-[A-Za-z0-9_-]{20,}\b"),
    "openai-token": re.compile(rb"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
    "slack-token": re.compile(rb"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    "jwt": re.compile(
        rb"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"
    ),
    "secret-like-assignment": re.compile(
        rb"(?im)^[ \t]*(?:export[ \t]+)?"
        rb"(?:[a-z0-9]+[_-])*"
        rb"(?:password[_-]?hash|password|passphrase|client[_-]?secret|"
        rb"api[_-]?key|access[_-]?token|refresh[_-]?token|secret[_-]?key|"
        rb"private[_-]?key|credential|secret)[ \t]*[:=][ \t]*[\"']?"
        rb"(?!(?:\$|\{\{|secret://|env://|<|"
        rb"false\b|true\b|null\b|none\b|example\b|placeholder\b|redacted\b|"
        rb"disabled(?:\b|[-_])|deferred(?:\b|[-_])|pending(?:\b|[-_])|"
        rb"change[-_]?me\b|not-a-real-secret\b))"
        rb"[^\s\"'#]{8,}",
        re.IGNORECASE,
    ),
    "credential-in-uri": re.compile(
        rb"\b(?:https?|postgres(?:ql)?|mysql|redis|amqps?)://"
        rb"[^\s/:@]+:[^\s/@]+@",
        re.IGNORECASE,
    ),
}


def content_findings(
    content: bytes,
    *,
    allowed_assignment_line_hashes: frozenset[str] = frozenset(),
) -> Iterator[str]:
    for rule_name, rule in CONTENT_RULES.items():
        if rule_name != "secret-like-assignment":
            if rule.search(content):
                yield rule_name
            continue

        unapproved_match = False
        for match in rule.finditer(content):
            line_start = content.rfind(b"\n", 0, match.start()) + 1
            line_end = content.find(b"\n", match.end())
            if line_end < 0:
                line_end = len(content)
            normalized_line = content[line_start:line_end].strip()
            line_sha256 = hashlib.sha256(normalized_line).hexdigest()
            if line_sha256 not in allowed_assignment_line_hashes:
                unapproved_match = True
                break
        if unapproved_match:
            yield rule_name

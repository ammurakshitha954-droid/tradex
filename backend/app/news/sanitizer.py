"""
Security Sanitizer for External Financial News & Social Data.
Defends against prompt injection, jailbreaks, and adversarial strings in untrusted web/news text.
"""
import re
from typing import List, Optional


class NewsSanitizer:
    # Adversarial patterns commonly found in prompt injection attacks
    SUSPICIOUS_PATTERNS = [
        r"(?i)ignore\s+(all\s+)?(previous|prior)\s+instructions",
        r"(?i)system\s+prompt",
        r"(?i)you\s+are\s+now\s+in\s+developer\s+mode",
        r"(?i)override\s+risk\s+guardian",
        r"(?i)always\s+(buy|sell|approve)",
        r"(?i)execute\s+order\s+immediately",
        r"(?i)bypass\s+limits?",
        r"<script.*?>.*?</script>",
        r"javascript:",
        r"\{\{.*?\}\}",  # Template injections
    ]

    @classmethod
    def sanitize_text(cls, text: str, max_chars: int = 2000) -> str:
        """
        Sanitizes untrusted financial text, strips prompt-injection markers and HTML/control characters.
        """
        if not text:
            return ""

        # Truncate length
        cleaned = text[:max_chars]

        # Strip html tags
        cleaned = re.sub(r"<[^>]+>", " ", cleaned)

        # Neutralize injection attempts
        for pattern in cls.SUSPICIOUS_PATTERNS:
            cleaned = re.sub(pattern, "[FILTERED_UNTRUSTED_CONTENT]", cleaned)

        # Strip non-printable / control characters (preserve normal punctuation)
        cleaned = "".join(ch for ch in cleaned if ch.isprintable() or ch in "\n\t")

        # Normalize whitespace
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

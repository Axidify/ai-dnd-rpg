"""
Whole-word keyword matching for rule detection.

Plain substring checks (``"bow" in text``) misfire on words that merely
contain a keyword ("crossbow", "force" -> "orc"). Every rule that scans
free text for keywords should go through these helpers instead.
"""

import re
from functools import lru_cache
from typing import Iterable, Optional

# Single words this long or longer also match common inflections
# ("hide" -> "hides", "climb" -> "climbing"). Shorter words match exactly,
# so "hi" never matches "his".
_INFLECT_MIN_LEN = 4
_INFLECTIONS = r"(?:s|es|ed|d|ing)?"


@lru_cache(maxsize=2048)
def _compile(phrase: str) -> re.Pattern:
    words = phrase.strip().lower().split()
    body = r"\s+".join(re.escape(w) for w in words)
    if len(words) == 1 and len(words[0]) >= _INFLECT_MIN_LEN and words[0].isalpha():
        body += _INFLECTIONS
    return re.compile(rf"(?<![\w']){body}(?![\w'])")


def has_phrase(text: str, phrase: str) -> bool:
    """True if ``phrase`` appears in ``text`` as whole word(s)."""
    return bool(_compile(phrase).search(text.lower()))


def find_phrase(text: str, phrases: Iterable[str]) -> Optional[str]:
    """Return the first phrase found in ``text`` as whole word(s), else None."""
    lowered = text.lower()
    for phrase in phrases:
        if _compile(phrase).search(lowered):
            return phrase
    return None


def has_any(text: str, phrases: Iterable[str]) -> bool:
    """True if any phrase appears in ``text`` as whole word(s)."""
    return find_phrase(text, phrases) is not None

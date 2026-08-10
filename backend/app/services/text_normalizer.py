"""
Text normalization.

Deliberately minimal: normalization must not destroy signal that later
phases measure (e.g. curly vs. straight quotes, em-dash usage, and other
punctuation choices are candidate rhythm/punctuation features per
docs/methodology.md, Section 6B of the project brief). This module only
canonicalizes representation and strips content that cannot be
meaningfully analyzed or safely rendered — it does not "clean up" style.
"""

import re
import unicodedata

# C0 control characters other than \n and \t, plus DEL. These can appear
# from malformed paste input and have no linguistic meaning to analyze.
_CONTROL_CHARS_RE = re.compile(
    "[" + "".join(chr(c) for c in range(0x00, 0x20) if chr(c) not in "\n\t") + "\x7f" + "]"
)


def normalize_text(text: str) -> str:
    """Canonicalize essay text before segmentation/analysis.

    - Unicode NFC normalization (canonicalizes representation, e.g.
      combining accents, without altering visible characters or
      substituting punctuation like NFKC would).
    - Line endings normalized to \\n.
    - Stray control characters removed.

    Whitespace runs, casing, and punctuation choices are preserved
    unchanged, since those are exactly what later feature extraction
    measures.
    """
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _CONTROL_CHARS_RE.sub("", text)
    return text

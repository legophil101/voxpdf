import re


def remove_control_characters(text: str) -> str:
    r"""
    Removes invisible/non-printable control characters that commonly appear in PDFs.

    Why this matters:
    Some TTS engines interpret characters like:
        - \x00 (NULL)
        - \x0c (Form Feed)
    as "End of Input", causing silent audio cutoffs.

    This is the #1 fix for the "audio stops mid-book" bug.
    """
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)


def normalize_symbols(text: str) -> str:
    r"""
    Normalize problematic symbols into TTS-friendly punctuation.

    Why:
    TTS engines struggle with uncommon Unicode symbols.
    Converting them improves speech flow and prevents glitches.
    """

    # Normalize bullets → sentence breaks
    text = re.sub(r'[●•]', '. ', text)

    # Normalize dashes → pauses
    text = re.sub(r'[—–]|--', ', ', text)

    # Normalize ellipses
    text = re.sub(r'…|\.\.+', '... ', text)

    return text


def fix_wide_text(text: str) -> str:
    r"""
    Collapses spaced-out words like:
        "C H A P T E R" → "CHAPTER"

    Only targets sequences of single letters to avoid breaking normal text.
    """
    pattern = r'(?:(?<=\s)|^)(?:[a-zA-Z]\s){2,}[a-zA-Z](?=\s|$)'

    def collapse(match):
        return match.group(0).replace(" ", "")

    return re.sub(pattern, collapse, text)


def fix_drop_caps(text: str) -> str:
    r"""
    Fixes drop cap formatting from PDFs:
        "N early" → "Nearly"

    Avoids breaking valid phrases like:
        "A dog", "I think"
    """
    return re.sub(r'\b([B-HJ-Z])\s+([a-z]+)\b', r'\1\2', text)


def fix_hyphenation(text: str) -> str:
    r"""
    Fixes words split across lines:
        "extra-\nordinary" → "extraordinary"
        "read- ing" → "reading"
    """
    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
    text = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', text)
    return text


def preserve_paragraphs(text: str) -> str:
    r"""
    Preserves paragraph breaks for better TTS pacing.

    Strategy:
    - Temporarily replace multiple newlines with a marker
    - Clean text
    - Restore paragraph spacing
    """
    # Normalize line endings
    text = text.replace('\r\n', '\n')

    # Mark paragraphs
    text = re.sub(r'\n{2,}', '<<PARA>>', text)

    # Flatten single line breaks
    text = re.sub(r'\n', ' ', text)

    # Restore paragraphs
    text = text.replace('<<PARA>>', '\n\n')

    return text


def remove_artifacts(text: str) -> str:
    r"""
    Removes unwanted artifacts from PDFs:
        - Markdown-like symbols (*, _)
        - URLs
        - random noise characters
    """
    text = re.sub(r'[\*_]{1,}', '', text)
    text = re.sub(r'http[s]?://\S+', '', text)
    return text


def normalize_whitespace(text: str) -> str:
    r"""
    Normalizes whitespace WITHOUT destroying paragraph structure.

    - Collapses multiple spaces/tabs into a single space
    - Preserves newlines (\n and \n\n) for TTS pauses

    Why:
    Using \s+ would collapse newlines and remove paragraph pauses,
    making speech sound flat and unnatural.
    """

    # Collapse spaces and tabs ONLY (not newlines)
    text = re.sub(r'[ \t]+', ' ', text)

    # Clean spaces around newlines
    text = re.sub(r' *\n *', '\n', text)

    # Limit excessive newlines (e.g., 5 → 2)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def ensure_sentence_spacing(text: str) -> str:
    r"""
    Ensures there is a space after sentence-ending punctuation.

    Example:
        "Hello.World" → "Hello. World"
    """
    return re.sub(r'([.!?])([A-Za-z])', r'\1 \2', text)


def strip_footnotes(text: str) -> str:
    """
    Removes superscript-style footnote references (e.g., 'types:7' -> 'types:').

    Why:
    Footnotes in PDFs are extracted as regular numbers touching the previous word.
    This regex targets 1-2 digit numbers preceded by a letter or punctuation.
    """
    # Pattern logic:
    # (?<=[a-zA-Z”.,:;]) -> Lookbehind: must follow a letter, quote, or punctuation
    # \d{1,2}            -> Match 1 or 2 digits (footnotes are rarely 3+ digits)
    # \b                 -> Word boundary: ensure it's not the start of a longer number
    return re.sub(r'(?<=[a-zA-Z”.,:;])\d{1,2}\b', '', text)


def clean_text(text: str, debug: bool = False) -> str:
    r"""
    MASTER CLEANING PIPELINE

    This function transforms raw PDF-extracted text into a
    TTS-optimized format suitable for high-quality audiobook generation.

    Pipeline Stages:

    1. SANITIZATION (critical for stability)
       - Remove control characters (prevents silent audio cutoffs)

    2. STRUCTURAL FIXES
       - Fix drop caps
       - Fix wide/spaced text
       - Fix hyphenation issues

    3. NORMALIZATION
       - Replace problematic symbols
       - Improve punctuation for speech flow

    4. FORMATTING
       - Preserve paragraph pauses
       - Remove artifacts (URLs, markdown noise)

    5. FINAL POLISH
       - Normalize whitespace

    This layered approach ensures:
        ✅ No silent truncation bugs
        ✅ Natural speech flow
        ✅ Clean, production-ready text

    Args:
        text (str): Raw text extracted from PDF

    Returns:
        str: Cleaned and TTS-ready text
    """
    if not text:
        return ""

    if debug:
        print("Original:", text[:300])

    # 1. CRITICAL: Prevent silent TTS cutoff
    text = remove_control_characters(text)

    if debug:
        print("After control cleanup:", text[:300])

    # 2. Structural fixes
    text = fix_drop_caps(text)
    text = fix_wide_text(text)
    text = fix_hyphenation(text)

    # 3. Normalize symbols for TTS
    text = normalize_symbols(text)

    # 4. Sentence correctness
    text = ensure_sentence_spacing(text)

    # 5. Preserve structure
    text = preserve_paragraphs(text)

    # 6. Remove noise
    text = remove_artifacts(text)

    # 7. New Footnote stripping step
    text = strip_footnotes(text)

    # 8. Final cleanup
    text = normalize_whitespace(text)

    return text

"""British-English speech normalisation for TTS.

Pure Python, no third-party imports. Intended to run immediately before
synthesis so the on-screen text is left unchanged.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

_ORDINALS = {
    1: "First",
    2: "Second",
    3: "Third",
    4: "Fourth",
    5: "Fifth",
    6: "Sixth",
    7: "Seventh",
    8: "Eighth",
    9: "Ninth",
    10: "Tenth",
}

_SMALL = {
    0: "zero",
    1: "one",
    2: "two",
    3: "three",
    4: "four",
    5: "five",
    6: "six",
    7: "seven",
    8: "eight",
    9: "nine",
    10: "ten",
    11: "eleven",
    12: "twelve",
}

# spoken form, and the "and a ..." form used after a whole number
_UNICODE_FRACTIONS = {
    "½": ("a half", "and a half"),
    "¼": ("a quarter", "and a quarter"),
    "¾": ("three quarters", "and three quarters"),
    "⅓": ("a third", "and a third"),
    "⅔": ("two thirds", "and two thirds"),
    "⅛": ("an eighth", "and an eighth"),
    "⅜": ("three eighths", "and three eighths"),
    "⅝": ("five eighths", "and five eighths"),
    "⅞": ("seven eighths", "and seven eighths"),
}

_ASCII_FRACTIONS = {
    (1, 2): ("a half", "and a half"),
    (1, 3): ("a third", "and a third"),
    (2, 3): ("two thirds", "and two thirds"),
    (1, 4): ("a quarter", "and a quarter"),
    (3, 4): ("three quarters", "and three quarters"),
    (1, 5): ("a fifth", "and a fifth"),
    (2, 5): ("two fifths", "and two fifths"),
    (1, 8): ("an eighth", "and an eighth"),
    (3, 8): ("three eighths", "and three eighths"),
    (5, 8): ("five eighths", "and five eighths"),
    (7, 8): ("seven eighths", "and seven eighths"),
}

# Longer unit spellings first. All matched only immediately after a number.
# British English spellings (litre, gram, etc.).
_UNIT_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"tbspn?s?|tbs\b", "tablespoon"),
    (r"tspn?s?", "teaspoon"),
    (r"lbs?|pounds?", "pound"),
    (r"ozs?|ounces?", "ounce"),
    (r"kgs?|kilograms?", "kilogram"),
    (r"mgs?|milligrams?", "milligram"),
    (r"mls?|millilitres?|milliliters?", "millilitre"),
    (r"cls?|centilitres?|centiliters?", "centilitre"),
    (r"cms?|centimetres?|centimeters?", "centimetre"),
    (r"mms?|millimetres?|millimeters?", "millimetre"),
    (r"ltrs?|litres?|liters?", "litre"),
    (r"grs?\b|grams?", "gram"),
)

_TIME_RE = re.compile(r"\b(\d{1,2}:\d{2}(?::\d{2})?)\b")
_URL_RE = re.compile(
    r"https?://[^\s<>\]]+|www\.[^\s<>\]]+",
    re.IGNORECASE,
)
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_MD_BOLD_RE = re.compile(r"(\*\*|__)(.*?)\1", re.DOTALL)
_MD_ITALIC_RE = re.compile(r"(?<!\w)([*_])([^*_\n]+)\1(?!\w)")
_MD_CODE_RE = re.compile(r"`+([^`]*)`+")
_MD_HEADING_RE = re.compile(r"(?m)^[ \t]{0,3}#{1,6}[ \t]+")
_MD_HR_RE = re.compile(r"(?m)^[ \t]{0,3}(?:-{3,}|\*{3,}|_{3,})[ \t]*$")
_TABLE_PIPE_RE = re.compile(r"[ \t]*\|[ \t]*")
_APPROX_RE = re.compile(r"\bapprox\b\.?", re.IGNORECASE)
_EG_RE = re.compile(r"\be\.g\.?,?", re.IGNORECASE)
_IE_RE = re.compile(r"\bi\.e\.?,?", re.IGNORECASE)

# Number used as a quantity (not a time — those are protected first).
_QUANTITY_RE = re.compile(
    r"(?<![\w.])(?P<num>\d+(?:\.\d+)?)"
)

# Mixed ascii fraction: "1 1/2" or "1-1/2"
_MIXED_ASCII_FRAC_RE = re.compile(
    r"(?<![\w.])(?P<whole>\d+)[ \t-]+(?P<num>\d+)\s*/\s*(?P<den>\d+)(?!\d)"
)
_ASCII_FRAC_RE = re.compile(
    r"(?<![\w./])(?P<num>\d+)\s*/\s*(?P<den>\d+)(?!\d)"
)
_MIXED_UNI_FRAC_RE = re.compile(
    r"(?<![\w.])(?P<whole>\d+)\s*(?P<frac>[{}])".format("".join(_UNICODE_FRACTIONS))
)
_UNI_FRAC_RE = re.compile(r"[{}]".format("".join(_UNICODE_FRACTIONS)))

# Short quantity ranges, not years or ISO dates (4-digit left side).
_RANGE_RE = re.compile(
    r"(?<![\w.-])(?P<a>\d{1,3}(?:\.\d+)?)[ \t]*[–—-][ \t]*(?P<b>\d{1,3}(?:\.\d+)?)(?![\w.-])"
)

# x2 / ×2 / x 2 (multiplier), and 2x
_MULT_LEFT_RE = re.compile(
    r"(?<![\w.])[x×][ \t]*(?P<n>\d+(?:\.\d+)?)(?![\w.])",
    re.IGNORECASE,
)
_MULT_RIGHT_RE = re.compile(
    r"(?<![\w.])(?P<n>\d+(?:\.\d+)?)[ \t]*[x×](?![\w.])",
    re.IGNORECASE,
)

# Numbered list markers at line start, or after sentence punctuation
# (flattened lists like "tins. 2. Cream"). Not decimals (1.5).
_LINE_NUM_RE = re.compile(
    r"(?m)(?P<prefix>^|(?<=\A)|(?<=[\n.!?]))(?P<space>[ \t]*)(?P<n>\d{1,3})(?P<mark>[.)])(?P<ws>[ \t]+)"
)
_LINE_BULLET_RE = re.compile(
    r"(?m)(?P<prefix>^|(?<=\A)|(?<=[\n:!?.]))(?P<space>[ \t]*)(?P<mark>[-*•]|#{1,6})(?P<ws>[ \t]+)"
)

# Degree temperatures: 180°C, 180 ºC, 180C, 180 F, 350°F
_TEMP_RE = re.compile(
    r"(?<![\w.])(?P<num>\d+(?:\.\d+)?)[ \t]*(?P<sym>[°º˚])?[ \t]*(?P<unit>[CF])(?![A-Za-z])"
)

_PERCENT_RE = re.compile(
    r"(?<![\w.])(?P<num>\d+(?:\.\d+)?)[ \t]*%"
)

# Incomplete token at the end of a stream buffer — hold it back.
_UNSAFE_TAIL_RE = re.compile(
    r"(?:"
    r"\d+$"  # bare number, maybe unit follows
    r"|\d+[ \t]*[./–—-]$"  # fraction or range in progress
    r"|\d+[.)]$"  # list marker without following space yet
    r"|\d+[ \t]+$"  # number then space, unit may follow
    r"|[°º˚]$"
    r"|https?:$|https?://\S*$|www\.\S*$"
    r"|\bapprox$|\be$|\be\.$|\bi$|\bi\.$"
    r"|[*_#`(\[]+$"
    r"|[x×]$"
    r")",
    re.IGNORECASE,
)


def _placeholder_protect(text: str, pattern: re.Pattern[str], prefix: str) -> tuple[str, dict[str, str]]:
    held: dict[str, str] = {}

    def repl(match: re.Match[str]) -> str:
        key = f"⟦{prefix}{len(held)}⟧"
        held[key] = match.group(0)
        return key

    return pattern.sub(repl, text), held


def _restore(text: str, held: dict[str, str]) -> str:
    for key, value in held.items():
        text = text.replace(key, value)
    return text


def _words_for_small(n: int) -> str:
    return _SMALL.get(n, str(n))


def _fraction_words(numer: int, denom: int, *, mixed: bool) -> str | None:
    pair = _ASCII_FRACTIONS.get((numer, denom))
    if not pair:
        return None
    return pair[1] if mixed else pair[0]


def _pluralise(unit: str, quantity: str) -> str:
    """British cooking usage: 1 / a half -> singular; 1.5 / two -> plural."""
    q = quantity.strip().lower()
    singular_forms = {
        "1",
        "1.0",
        "a",
        "an",
        "one",
        "a half",
        "a quarter",
        "a third",
        "an eighth",
        "a fifth",
        "zero",
        "0",
    }
    if q in singular_forms or q.startswith("a ") or q.startswith("an "):
        return unit
    return unit + "s"



_SPOKEN_QTY_RE = re.compile(
    r"(?P<qty>"
    r"a half|a quarter|a third|an eighth|a fifth|"
    r"two thirds|three quarters|three eighths|five eighths|seven eighths|"
    r"one and a half|two and a half|three and a half|four and a half|"
    r"one and a quarter|two and a quarter|"
    r"one and three quarters|two and three quarters"
    r")[ \t]*(?P<unit>tbspn?s?|tbs\b|tspn?s?|lbs?|ozs?|kgs?|mgs?|mls?|cls?|cms?|mms?|ltrs?|grs?\b|grams?|g\b|l\b|t\b)",
    re.IGNORECASE,
)


def _expand_units_after_words(text: str) -> str:
    """Expand units that follow a spoken fraction rather than a digit."""
    compiled_units = [(re.compile(rf"^(?:{p})$", re.IGNORECASE), name) for p, name in _UNIT_PATTERNS]

    def unit_name(raw: str) -> str | None:
        token = raw.strip()
        for cre, name in compiled_units:
            if cre.match(token):
                return name
        low = token.lower()
        if low == "g":
            return "gram"
        if low == "l":
            return "litre"
        if low == "t":
            return "tablespoon" if token == "T" else "teaspoon"
        return None

    def repl(match: re.Match[str]) -> str:
        qty = match.group("qty")
        name = unit_name(match.group("unit"))
        if not name:
            return match.group(0)
        return f"{qty} {_pluralise(name, qty)}"

    return _SPOKEN_QTY_RE.sub(repl, text)


def _expand_units(text: str) -> str:
    # Build a single regex of number + optional space + unit, longer units first.
    unit_alt = "|".join(p for p, _ in _UNIT_PATTERNS)
    # Bare 'g' (grams) and 'l'/'L' (litres) and 't'/'T' (tea/table spoon).
    # 'g' must not eat the start of a normal word (already ensured by unit \b).
    # Standalone 'I' is not a number so it will never match.
    bare = r"g\b|l\b|t\b"
    pattern = re.compile(
        rf"(?<![\w.])(?P<num>\d+(?:\.\d+)?)[ \t]*(?P<unit>(?:{unit_alt})|{bare})(?![A-Za-z])",
        re.IGNORECASE,
    )
    compiled_units = [(re.compile(rf"^(?:{p})$", re.IGNORECASE), name) for p, name in _UNIT_PATTERNS]

    def unit_name(raw: str) -> str | None:
        token = raw.strip()
        for cre, name in compiled_units:
            if cre.match(token):
                return name
        low = token.lower()
        if low == "g":
            return "gram"
        if low == "l":
            return "litre"
        if low == "t":
            # Capital T is tablespoon in recipe shorthand; lowercase t is teaspoon.
            return "tablespoon" if token == "T" else "teaspoon"
        return None

    def repl(match: re.Match[str]) -> str:
        num = match.group("num")
        name = unit_name(match.group("unit"))
        if not name:
            return match.group(0)
        return f"{num} {_pluralise(name, num)}"

    return pattern.sub(repl, text)


def _expand_temperatures(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        num = match.group("num")
        unit = match.group("unit").upper()
        # Require a degree symbol, or a tightly packed 180C / 350F (no space).
        # "180 C" without a degree mark is left alone to avoid false hits.
        has_sym = bool(match.group("sym"))
        tight = match.group(0).find(" ") == -1 and match.group(0).find("\t") == -1
        if not has_sym and not tight:
            return match.group(0)
        scale = "Celsius" if unit == "C" else "Fahrenheit"
        return f"{num} degrees {scale}"

    return _TEMP_RE.sub(repl, text)


def _expand_fractions(text: str) -> str:
    def mixed_ascii(match: re.Match[str]) -> str:
        whole = int(match.group("whole"))
        words = _fraction_words(int(match.group("num")), int(match.group("den")), mixed=True)
        if not words:
            return match.group(0)
        return f"{_words_for_small(whole)} {words}"

    text = _MIXED_ASCII_FRAC_RE.sub(mixed_ascii, text)

    def mixed_uni(match: re.Match[str]) -> str:
        frac = match.group("frac")
        spoken = _UNICODE_FRACTIONS[frac][1]
        whole = int(match.group("whole"))
        return f"{_words_for_small(whole)} {spoken}"

    text = _MIXED_UNI_FRAC_RE.sub(mixed_uni, text)

    def ascii_frac(match: re.Match[str]) -> str:
        words = _fraction_words(int(match.group("num")), int(match.group("den")), mixed=False)
        return words if words else match.group(0)

    text = _ASCII_FRAC_RE.sub(ascii_frac, text)

    def uni_frac(match: re.Match[str]) -> str:
        return _UNICODE_FRACTIONS[match.group(0)][0]

    return _UNI_FRAC_RE.sub(uni_frac, text)


def _list_label(n: int) -> str:
    if n <= 0:
        return "Next,"
    if n in _ORDINALS:
        return _ORDINALS[n] + ","
    if n <= 20:
        return f"Step {_words_for_small(n)},"
    return "Next,"


def _expand_list_markers(text: str) -> str:
    def num_repl(match: re.Match[str]) -> str:
        n = int(match.group("n"))
        prefix = match.group("prefix")
        # Keep a space after sentence punctuation so "tins. Second," reads cleanly.
        gap = " " if prefix in ".!?" or (prefix and prefix[-1:] in ".!?") else ""
        if prefix and prefix not in ("", "\n") and prefix[-1:] in ".!?":
            gap = " "
        return f"{prefix}{gap}{_list_label(n)} "

    text = _LINE_NUM_RE.sub(num_repl, text)

    def bullet_repl(match: re.Match[str]) -> str:
        prefix = match.group("prefix")
        mark = match.group("mark")
        # Headings were already stripped; remaining # at line start is a bullet.
        gap = " " if prefix and prefix[-1:] in ":.!?" else ""
        # Unordered markers: a spoken "Next," is clearer than a punctuation click,
        # and avoids inventing First/Second that would collide with later steps.
        if mark.startswith("#") and len(mark) > 1:
            # leftover heading hashes
            return f"{prefix}{gap}"
        return f"{prefix}{gap}Next, "

    return _LINE_BULLET_RE.sub(bullet_repl, text)


def _strip_markdown(text: str) -> str:
    text = _MD_LINK_RE.sub(lambda m: m.group(1), text)
    text = _URL_RE.sub("link", text)
    text = _MD_CODE_RE.sub(lambda m: m.group(1), text)
    text = _MD_BOLD_RE.sub(lambda m: m.group(2), text)
    text = _MD_ITALIC_RE.sub(lambda m: m.group(2), text)
    text = _MD_HEADING_RE.sub("", text)
    text = _MD_HR_RE.sub("", text)
    # Table rows: pipes to commas, drop separator-only lines
    lines = []
    for line in text.splitlines(keepends=True):
        raw = line.strip()
        if raw and set(raw.replace("|", "").replace("-", "").replace(":", "").replace(" ", "")) == set():
            if "|" in raw or re.fullmatch(r"[:\- ]+", raw):
                continue
        if "|" in line:
            stripped = line.strip()
            if stripped.startswith("|"):
                stripped = stripped[1:]
            if stripped.endswith("|"):
                stripped = stripped[:-1]
            cells = [c.strip() for c in stripped.split("|")]
            ending = "\n" if line.endswith("\n") else ""
            line = ", ".join(c for c in cells if c) + ending
        lines.append(line)
    return "".join(lines)


def _tidy_whitespace(text: str) -> str:
    # Preserve paragraph breaks as a short pause (period-equivalent space).
    text = re.sub(r"\n{2,}", ". ", text)
    text = text.replace("\n", " ")
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\s+([,;:])", r"\1", text)
    text = re.sub(r"\s+\.", ".", text)
    text = re.sub(r"\.{2,}", ".", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def normalize_for_speech(text: str) -> str:
    """Return a spoken-English rendering of *text* (British English).

    Safe to call on a complete utterance. Empty input stays empty.
    """
    if not text or not text.strip():
        return ""

    text, times = _placeholder_protect(text, _TIME_RE, "TIME")
    text = _strip_markdown(text)
    text = _expand_list_markers(text)
    text = _expand_fractions(text)
    text = _RANGE_RE.sub(lambda m: f"{m.group('a')} to {m.group('b')}", text)
    text = _MULT_LEFT_RE.sub(lambda m: f"times {_words_for_small(int(m.group('n'))) if m.group('n').isdigit() and int(m.group('n')) in _SMALL else m.group('n')}", text)
    # 2x after x2, so we don't double-hit
    text = _MULT_RIGHT_RE.sub(
        lambda m: (
            f"{m.group('n')} times"
            if not m.group(0).lower().startswith("times")
            else m.group(0)
        ),
        text,
    )
    text = _expand_temperatures(text)
    text = _PERCENT_RE.sub(lambda m: f"{m.group('num')} percent", text)
    text = _expand_units(text)
    text = _expand_units_after_words(text)
    text = _APPROX_RE.sub("approximately", text)
    text = _EG_RE.sub("for example", text)
    text = _IE_RE.sub("that is", text)
    text = text.replace("&", " and ")
    text = _restore(text, times)
    return _tidy_whitespace(text)


def _safe_split(buffer: str) -> tuple[str, str]:
    """Split *buffer* into a flushable prefix and a held remainder."""
    if not buffer:
        return "", ""
    # Prefer flushing complete lines.
    if "\n" in buffer:
        head, tail = buffer.rsplit("\n", 1)
        # Keep the newline with the head so list-start markers stay at line start.
        head = head + "\n"
        if tail and _UNSAFE_TAIL_RE.search(tail):
            return head, tail
        # If the tail is a complete enough phrase ending with punctuation, flush all.
        if tail and re.search(r"[.!?]$", tail):
            return buffer, ""
        return head, tail
    if _UNSAFE_TAIL_RE.search(buffer):
        return "", buffer
    # Flush up to the last sentence boundary if the tail looks unfinished.
    match = None
    for match in re.finditer(r"[.!?]\s+", buffer):
        pass
    if match:
        return buffer[: match.end()], buffer[match.end() :]
    return buffer, ""


class StreamingNormalizer:
    """Accumulate streamed TTS text and emit speech-ready segments.

    Home Assistant's Wyoming client may send token-sized SynthesizeChunk
    events (so a marker like ``1.`` or a unit like ``225g`` can be split
    across chunks) and then a backwards-compatible full ``Synthesize``.
    Buffer until a safe boundary, or until :meth:`flush` at end of utterance.
    """

    def __init__(self) -> None:
        self._buf = ""

    def reset(self) -> None:
        self._buf = ""

    def feed(self, chunk: str) -> str:
        if not chunk:
            return ""
        self._buf += chunk
        flushable, self._buf = _safe_split(self._buf)
        return normalize_for_speech(flushable) if flushable.strip() else ""

    def flush(self) -> str:
        text = self._buf
        self._buf = ""
        return normalize_for_speech(text) if text.strip() else ""

    def peek(self) -> str:
        return self._buf


def normalize_chunks(chunks: Iterable[str]) -> str:
    """Normalise a sequence of streamed chunks as one utterance (for tests)."""
    stream = StreamingNormalizer()
    parts: list[str] = []
    for chunk in chunks:
        out = stream.feed(chunk)
        if out:
            parts.append(out)
    tail = stream.flush()
    if tail:
        parts.append(tail)
    return _tidy_whitespace(" ".join(parts))

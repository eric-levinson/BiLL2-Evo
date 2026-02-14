import re

try:
    from unidecode import unidecode  # optional, better accent handling
except Exception:
    unidecode = None  # type: Optional[object]

_suffix_re = re.compile(r"\b(jr|sr|ii|iii|iv|v)\b\.?", flags=re.I)
_punct_re = re.compile(r"[^A-Za-z0-9\s-]")
_spaces_re = re.compile(r"\s+")


def sanitize_name(name: str) -> str:
    """Normalize a player name for safe ILIKE matching."""
    s = name or ""
    if unidecode:
        s = unidecode(s)
    s = _suffix_re.sub("", s)
    s = _punct_re.sub("", s)
    s = _spaces_re.sub(" ", s).strip()
    return s.lower()

"""Shared conservative alias lookup. No I/O and no hard-block policy changes."""
from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from typing import Any

# These existing generic labels remain usable by exact match only.
_EXACT_ONLY = frozenset({
    'beyond', 'confidencial', 'encanto', 'marketstrat', 'viva', 'yello',
})


def _normalize(value: str) -> str:
    return ' '.join(unicodedata.normalize('NFKC', value).casefold().split())


def _identity(entry: Mapping[str, Any]) -> tuple[Any, Any, bool]:
    return entry.get('marca'), entry.get('holding'), bool(entry.get('hard_block', False))


def _unique(entries: list[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    first = entries[0]
    return first if all(_identity(e) == _identity(first) for e in entries) else None


def resolve_alias_entry(
    raw: str | None, alias_data: Mapping[str, Any],
) -> Mapping[str, Any] | None:
    """Exact first; then complete bounded phrases, never reverse substrings.

    Keys with at most four alphanumeric characters and generic labels are
    exact-only. A phrase fully contained in a more specific matching phrase
    loses to that phrase. Distinct remaining identities are ambiguous and
    return None, regardless of JSON order. Flags are returned unchanged.
    """
    if not raw or not raw.strip():
        return None
    aliases = alias_data.get('aliases', {})
    # Preserve the existing exact spelling lookup before normalizing further.
    entry = aliases.get(raw.strip().lower())
    if entry:
        return entry
    key = _normalize(raw)
    normalized = [(_normalize(alias), value) for alias, value in aliases.items()]
    exact = [value for alias, value in normalized if alias == key]
    if exact:
        return _unique(exact)
    matches: list[tuple[int, int, Mapping[str, Any]]] = []
    for alias, value in normalized:
        if not alias or alias in _EXACT_ONLY:
            continue
        if sum(ch.isalnum() for ch in alias) <= 4:
            continue
        pattern = r'(?<!\w)' + re.escape(alias) + r'(?!\w)'
        for match in re.finditer(pattern, key):
            matches.append((match.start(), match.end(), value))
    if not matches:
        return None
    # Keep unrelated matches: choosing the longest globally would silently
    # guess one company in an input such as "Gucci / Louis Vuitton".
    survivors = [
        value for start, end, value in matches
        if not any(
            other_start <= start and end <= other_end
            and (other_start < start or end < other_end)
            for other_start, other_end, _ in matches
        )
    ]
    return _unique(survivors)

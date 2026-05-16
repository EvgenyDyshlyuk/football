"""In-memory match storage for the first local match workflow."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from itertools import count
from threading import Lock


@dataclass(frozen=True)
class Match:
    """A locally organized football match."""

    id: int
    creator_sub: str
    title: str
    starts_at: datetime
    location: str
    class_from: str
    class_to: str
    max_players: int
    notes: str

    @property
    def starts_at_label(self) -> str:
        """Display-friendly date and time."""
        return self.starts_at.strftime("%d %b %Y %H:%M")

    @property
    def class_range_label(self) -> str:
        """Display-friendly class range."""
        if self.class_from == self.class_to:
            return format_class(self.class_from)
        return f"{format_class(self.class_from)} to {format_class(self.class_to)}"


CLASS_OPTIONS = ("reception", "1", "2", "3", "4", "5", "6")

_MATCHES: list[Match] = []
_NEXT_ID = count(1)
_LOCK = Lock()


def format_class(value: str) -> str:
    """Return a display label for a school class value."""
    if value == "reception":
        return "Reception"
    return f"Year {value}"


def create_match(
    *,
    creator_sub: str,
    title: str,
    starts_at: datetime,
    location: str,
    class_from: str,
    class_to: str,
    max_players: int,
    notes: str,
) -> Match:
    """Create and store a match."""
    normalized_title = title.strip()
    normalized_location = location.strip()
    normalized_notes = notes.strip()

    if not normalized_title:
        raise ValueError("Match title is required")
    if not normalized_location:
        raise ValueError("Location is required")
    if class_from not in CLASS_OPTIONS or class_to not in CLASS_OPTIONS:
        raise ValueError("Class range is invalid")
    if CLASS_OPTIONS.index(class_from) > CLASS_OPTIONS.index(class_to):
        raise ValueError("Class range start must not be after the end")
    if max_players < 2 or max_players > 40:
        raise ValueError("Max players must be between 2 and 40")

    global _NEXT_ID
    with _LOCK:
        match = Match(
            id=next(_NEXT_ID),
            creator_sub=creator_sub,
            title=normalized_title,
            starts_at=starts_at,
            location=normalized_location,
            class_from=class_from,
            class_to=class_to,
            max_players=max_players,
            notes=normalized_notes,
        )
        _MATCHES.append(match)
        return match


def list_matches() -> list[Match]:
    """Return matches sorted by date."""
    with _LOCK:
        return sorted(_MATCHES, key=lambda match: (match.starts_at, match.id))


def clear_matches() -> None:
    """Clear all matches. Intended for tests and local development reset hooks."""
    global _NEXT_ID
    with _LOCK:
        _MATCHES.clear()
        _NEXT_ID = count(1)

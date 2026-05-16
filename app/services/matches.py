"""Match storage service with DynamoDB and local in-memory repositories."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from itertools import count
from threading import Lock
from typing import Any, Protocol
from uuid import uuid4

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import BotoCoreError, ClientError

from app.config import AWS_REGION, MATCHES_TABLE_NAME, MATCHES_USE_MEMORY


@dataclass(frozen=True)
class Match:
    """A locally organized football match."""

    id: str
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


class MatchRepository(Protocol):
    """Persistence boundary for matches."""

    def create(self, match: Match) -> Match:
        """Persist a match."""

    def list(self) -> list[Match]:
        """List stored matches."""

    def clear(self) -> None:
        """Clear stored matches. Intended for tests/local development."""


class MatchStorageError(RuntimeError):
    """Base error for match storage failures."""


class MatchStorageNotConfiguredError(MatchStorageError):
    """Raised when no match storage backend is configured."""


class InMemoryMatchRepository:
    """In-memory repository used for tests and local fallback."""

    def __init__(self) -> None:
        self._matches: list[Match] = []
        self._lock = Lock()
        self._next_id = count(1)

    def create(self, match: Match) -> Match:
        with self._lock:
            persisted = Match(
                id=str(next(self._next_id)),
                creator_sub=match.creator_sub,
                title=match.title,
                starts_at=match.starts_at,
                location=match.location,
                class_from=match.class_from,
                class_to=match.class_to,
                max_players=match.max_players,
                notes=match.notes,
            )
            self._matches.append(persisted)
            return persisted

    def list(self) -> list[Match]:
        with self._lock:
            return sorted(self._matches, key=lambda match: (match.starts_at, match.id))

    def clear(self) -> None:
        with self._lock:
            self._matches.clear()
            self._next_id = count(1)


class DynamoDBMatchRepository:
    """DynamoDB repository for production match storage."""

    partition_key = "MATCH"

    def __init__(self, table: Any) -> None:
        self.table = table

    @classmethod
    def from_table_name(cls, table_name: str) -> DynamoDBMatchRepository:
        table = boto3.resource("dynamodb", region_name=AWS_REGION).Table(table_name)
        return cls(table)

    def create(self, match: Match) -> Match:
        match_id = uuid4().hex
        persisted = Match(
            id=match_id,
            creator_sub=match.creator_sub,
            title=match.title,
            starts_at=match.starts_at,
            location=match.location,
            class_from=match.class_from,
            class_to=match.class_to,
            max_players=match.max_players,
            notes=match.notes,
        )
        try:
            self.table.put_item(Item=self._to_item(persisted))
        except (BotoCoreError, ClientError) as exc:
            raise MatchStorageError(
                "Unable to save match. Check DynamoDB table access and AWS credentials."
            ) from exc
        return persisted

    def list(self) -> list[Match]:
        try:
            response = self.table.query(
                KeyConditionExpression=Key("PK").eq(self.partition_key),
                ScanIndexForward=True,
            )
        except (BotoCoreError, ClientError) as exc:
            raise MatchStorageError(
                "Unable to load matches. Check DynamoDB table access and AWS credentials."
            ) from exc
        items = response.get("Items", [])
        return [self._from_item(item) for item in items]

    def clear(self) -> None:
        raise RuntimeError("Clearing DynamoDB matches from the app is not supported")

    def _to_item(self, match: Match) -> dict[str, Any]:
        starts_at_value = match.starts_at.isoformat(timespec="seconds")
        sort_key = f"START#{starts_at_value}#{match.id}"
        return {
            "PK": self.partition_key,
            "SK": sort_key,
            "GSI1PK": f"USER#{match.creator_sub}",
            "GSI1SK": sort_key,
            "match_id": match.id,
            "creator_sub": match.creator_sub,
            "title": match.title,
            "starts_at": starts_at_value,
            "location": match.location,
            "class_from": match.class_from,
            "class_to": match.class_to,
            "max_players": match.max_players,
            "notes": match.notes,
        }

    def _from_item(self, item: dict[str, Any]) -> Match:
        return Match(
            id=str(item["match_id"]),
            creator_sub=str(item["creator_sub"]),
            title=str(item["title"]),
            starts_at=datetime.fromisoformat(str(item["starts_at"])),
            location=str(item["location"]),
            class_from=str(item["class_from"]),
            class_to=str(item["class_to"]),
            max_players=int(item["max_players"]),
            notes=str(item.get("notes", "")),
        )


CLASS_OPTIONS = ("reception", "1", "2", "3", "4", "5", "6")

_repository: MatchRepository | None = None


def format_class(value: str) -> str:
    """Return a display label for a school class value."""
    if value == "reception":
        return "Reception"
    return f"Year {value}"


def get_match_repository() -> MatchRepository:
    """Return the configured match repository."""
    global _repository
    if _repository is None:
        if MATCHES_TABLE_NAME:
            _repository = DynamoDBMatchRepository.from_table_name(MATCHES_TABLE_NAME)
        elif MATCHES_USE_MEMORY:
            _repository = InMemoryMatchRepository()
        else:
            raise MatchStorageNotConfiguredError(
                "Match storage is not configured. Set MATCHES_TABLE_NAME to use "
                "DynamoDB, or set MATCHES_USE_MEMORY=true for local-only development."
            )
    return _repository


def set_match_repository(repository: MatchRepository | None) -> None:
    """Override the match repository. Intended for tests."""
    global _repository
    _repository = repository


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
    match = _build_match(
        creator_sub=creator_sub,
        title=title,
        starts_at=starts_at,
        location=location,
        class_from=class_from,
        class_to=class_to,
        max_players=max_players,
        notes=notes,
    )
    return get_match_repository().create(match)


def list_matches() -> list[Match]:
    """Return matches sorted by date."""
    return get_match_repository().list()


def clear_matches() -> None:
    """Clear all matches. Intended for tests and local development reset hooks."""
    get_match_repository().clear()


def _build_match(
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

    return Match(
        id="",
        creator_sub=creator_sub,
        title=normalized_title,
        starts_at=starts_at,
        location=normalized_location,
        class_from=class_from,
        class_to=class_to,
        max_players=max_players,
        notes=normalized_notes,
    )

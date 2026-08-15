"""Shared input and output bounds for the public MCP surface."""
from __future__ import annotations

from typing import Annotated

from pydantic import Field


TopK = Annotated[int, Field(ge=1, le=100, description="Number of search hits to return.")]
PageOffset = Annotated[int, Field(ge=0, le=100_000, description="Zero-based page offset.")]
PageSize = Annotated[int, Field(ge=1, le=200, description="Number of records in one page.")]
MaxChars = Annotated[int, Field(ge=256, le=60_000, description="Maximum returned text characters.")]
ProductCaseName = Annotated[
    str,
    Field(
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$",
        description="Local product case stem without a path or extension.",
    ),
]
ProductRecordWidth = Annotated[
    int,
    Field(ge=1, le=32, description="Numeric record width passed to the fixed product DLL API."),
]
ProductTimeout = Annotated[
    int,
    Field(ge=1, le=86_400, description="Hard timeout for the isolated product worker in seconds."),
]
LocalDirectoryPath = Annotated[
    str,
    Field(min_length=1, max_length=4096, description="Existing user-local directory path."),
]
OptionalProductHome = Annotated[
    str,
    Field(max_length=4096, description="Optional user-local product installation root."),
]
PositiveFloat = Annotated[
    float,
    Field(gt=0.0, allow_inf_nan=False, description="Finite value greater than zero."),
]
NonNegativeFloat = Annotated[
    float,
    Field(ge=0.0, allow_inf_nan=False, description="Finite value greater than or equal to zero."),
]


def bounded_int(value: int, *, name: str, minimum: int, maximum: int) -> int:
    """Return *value* when it is a real integer inside the closed interval."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    if value < minimum or value > maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return value


def positive_float(value: float, *, name: str) -> float:
    """Return a finite positive float or raise a stable validation error."""
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a finite number greater than zero") from exc
    if number <= 0.0 or number != number or number in (float("inf"), float("-inf")):
        raise ValueError(f"{name} must be a finite number greater than zero")
    return number


def page(items: list, *, offset: int = 0, limit: int = 100) -> tuple[list, dict[str, int | bool]]:
    """Apply a bounded page and return deterministic pagination metadata."""
    offset = bounded_int(offset, name="offset", minimum=0, maximum=100_000)
    limit = bounded_int(limit, name="limit", minimum=1, maximum=200)
    total = len(items)
    selected = items[offset : offset + limit]
    return selected, {
        "offset": offset,
        "limit": limit,
        "returned": len(selected),
        "total": total,
        "has_more": offset + len(selected) < total,
    }

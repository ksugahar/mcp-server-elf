"""Stable semantic response models for the canonical public MCP tools."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SearchHit(StrictModel):
    identifier: str
    title: str
    summary: str
    score: int = Field(ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchResponse(StrictModel):
    schema_version: Literal["elf.search.v1"] = "elf.search.v1"
    query: str
    source: str
    hits: list[SearchHit]
    total: int = Field(ge=0)
    truncated: bool = False


class ReadResponse(StrictModel):
    schema_version: Literal["elf.read.v1"] = "elf.read.v1"
    identifier: str
    title: str
    text: str
    truncated: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class PageResponse(StrictModel):
    schema_version: Literal["elf.page.v1"] = "elf.page.v1"
    source: str
    items: list[dict[str, Any]]
    offset: int = Field(ge=0)
    limit: int = Field(ge=1, le=200)
    returned: int = Field(ge=0)
    total: int = Field(ge=0)
    has_more: bool


class GateResponse(StrictModel):
    schema_version: Literal["elf.gate.v1"] = "elf.gate.v1"
    gate: str
    status: Literal["PASS", "WARN", "FAIL"]
    checks: dict[str, bool]
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    data: dict[str, Any] = Field(default_factory=dict)

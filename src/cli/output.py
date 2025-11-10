"""Output formatting utilities for the Discovery CLI."""

from __future__ import annotations

import json
from enum import Enum
from typing import Iterable, Mapping, Sequence

import yaml
from rich.console import Console
from rich.table import Table

console = Console()


class OutputFormat(str, Enum):
    """Supported output formats."""

    TABLE = "table"
    JSON = "json"
    YAML = "yaml"
    TEXT = "text"


def render_output(data, *, fmt: OutputFormat, title: str | None = None) -> None:
    if fmt == OutputFormat.JSON:
        console.print_json(data=data)
        return
    if fmt == OutputFormat.YAML:
        console.print(yaml.safe_dump(data, sort_keys=False))
        return
    if fmt == OutputFormat.TEXT:
        if isinstance(data, str):
            console.print(data)
        else:
            console.print(json.dumps(data, indent=2))
        return
    console.print(_build_table(data, title=title))


def _build_table(data, *, title: str | None = None) -> Table:
    table = Table(title=title, expand=True)
    rows: Iterable[Mapping]
    if isinstance(data, Mapping):
        table.add_column("Field")
        table.add_column("Value")
        for key, value in data.items():
            table.add_row(str(key), _to_text(value))
        return table
    if isinstance(data, Sequence):
        items = list(data)
        if not items:
            table.add_column("Result")
            return table
        if isinstance(items[0], Mapping):
            headers = list(items[0].keys())
            for header in headers:
                table.add_column(str(header))
            for item in items:
                table.add_row(*[_to_text(item.get(h)) for h in headers])
            return table
        table.add_column("Result")
        for item in items:
            table.add_row(_to_text(item))
        return table
    table.add_column("Result")
    table.add_row(_to_text(data))
    return table


def _to_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return ", ".join(_to_text(v) for v in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


__all__ = ["OutputFormat", "render_output", "console"]

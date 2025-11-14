"""Utility helpers for CLI commands."""

from __future__ import annotations

import base64
import json
import mimetypes
from pathlib import Path
from typing import Iterable, List, Sequence

import typer

from .exceptions import EditorLaunchError


def comma_separated(value: str | None) -> List[str] | None:
    if value is None:
        return None
    items = [item.strip() for item in value.split(",") if item.strip()]
    return items or None


def read_json_payload(path: Path) -> dict:
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise typer.BadParameter(f"Failed to read {path}: {exc}") from exc
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise typer.BadParameter(f"Invalid JSON in {path}: {exc}") from exc


def ensure_notebook_id(explicit: str | None, fallback: str | None, prompt: str = "Notebook ID") -> str:
    if explicit:
        return explicit
    if fallback:
        return fallback
    value = typer.prompt(prompt)
    if not value:
        raise typer.BadParameter("Notebook ID is required.")
    return value


def pick_file_type(path: Path) -> str:
    guessed, _ = mimetypes.guess_type(path.name)
    if guessed:
        if "pdf" in guessed:
            return "pdf"
        if "msword" in guessed or path.suffix.lower() in {".doc", ".docx"}:
            return "docx" if path.suffix.lower() == ".docx" else "doc"
        if "text" in guessed:
            return "txt"
    if path.suffix.lower() in {".md", ".markdown"}:
        return "md"
    raise typer.BadParameter("Unable to determine file type; use a supported extension (pdf, docx, doc, txt, md).")


def encode_file(path: Path) -> str:
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise typer.BadParameter(f"Failed to read file '{path}': {exc}") from exc
    return base64.b64encode(data).decode("utf-8")


def open_editor(initial_text: str | None = None) -> str:
    try:
        edited = typer.edit(text=initial_text or "")
    except OSError as exc:  # pragma: no cover - depends on environment
        raise EditorLaunchError(str(exc)) from exc
    if edited is None:
        raise EditorLaunchError("Editor aborted without content.")
    content = edited.strip()
    if not content:
        raise EditorLaunchError("No content provided.")
    return content


def list_to_rows(items: Sequence[dict], columns: Iterable[str]) -> List[dict]:
    return [{column: item.get(column) for column in columns} for item in items]


__all__ = [
    "comma_separated",
    "read_json_payload",
    "ensure_notebook_id",
    "pick_file_type",
    "encode_file",
    "open_editor",
    "list_to_rows",
]

"""Source management commands."""

from __future__ import annotations

from pathlib import Path

import typer

from ..output import OutputFormat, render_output, console
from ..runtime import RuntimeContext, load_runtime
from ..utils import encode_file, ensure_notebook_id, open_editor, pick_file_type

sources_app = typer.Typer(help="Manage notebook sources.")
add_app = typer.Typer(help="Add new sources.")
sources_app.add_typer(add_app, name="add")


def _context(profile: str | None) -> RuntimeContext:
    return load_runtime(profile)


@add_app.command("url")
def add_url_source(
    notebook: str | None = typer.Option(None, "--notebook", "-n", help="Notebook GUID"),
    url: str = typer.Option(..., "--url", prompt="Source URL"),
    title: str | None = typer.Option(None, "--title", help="Optional title override"),
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to use"),
    fmt: OutputFormat = typer.Option(OutputFormat.TABLE, "--format", "-f", case_sensitive=False),
) -> None:
    runtime = _context(profile)
    notebook_id = ensure_notebook_id(notebook, runtime.fallback_notebook())
    payload = {"notebook_id": notebook_id, "url": url, "title": title}
    with runtime.api_client() as client:
        response = client.post_json("/api/sources/url", json=payload)
    runtime.remember_notebook(notebook_id)
    render_output(response, fmt=fmt, title="URL Source Added")


@add_app.command("file")
def add_file_source(
    notebook: str | None = typer.Option(None, "--notebook", "-n", help="Notebook GUID"),
    path: Path = typer.Option(..., "--path", exists=True, dir_okay=False, readable=True, resolve_path=True, help="Path to file"),
    title: str | None = typer.Option(None, "--title", help="Optional title"),
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to use"),
    fmt: OutputFormat = typer.Option(OutputFormat.TABLE, "--format", "-f", case_sensitive=False),
) -> None:
    runtime = _context(profile)
    notebook_id = ensure_notebook_id(notebook, runtime.fallback_notebook())
    payload = {
        "notebook_id": notebook_id,
        "name": title or path.name,
        "file_content": encode_file(path),
        "file_type": pick_file_type(path),
    }
    with runtime.api_client(timeout=60.0) as client:
        response = client.post_json("/api/sources/file", json=payload)
    runtime.remember_notebook(notebook_id)
    render_output(response, fmt=fmt, title="File Source Added")


@add_app.command("text")
def add_text_source(
    notebook: str | None = typer.Option(None, "--notebook", "-n", help="Notebook GUID"),
    title: str = typer.Option(..., "--title", prompt="Text title"),
    content: str | None = typer.Option(None, "--content", help="Inline content"),
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to use"),
    fmt: OutputFormat = typer.Option(OutputFormat.TABLE, "--format", "-f", case_sensitive=False),
) -> None:
    runtime = _context(profile)
    notebook_id = ensure_notebook_id(notebook, runtime.fallback_notebook())
    if content is None:
        content = open_editor()
    payload = {"notebook_id": notebook_id, "title": title, "content": content}
    with runtime.api_client() as client:
        response = client.post_json("/api/sources/text", json=payload)
    runtime.remember_notebook(notebook_id)
    render_output(response, fmt=fmt, title="Text Source Added")


@sources_app.command("list")
def list_sources(
    notebook: str | None = typer.Option(None, "--notebook", "-n", help="Notebook GUID"),
    source_type: str | None = typer.Option(None, "--type", help="Filter by source type"),
    file_type: str | None = typer.Option(None, "--file-type", help="Filter by file type"),
    include_deleted: bool = typer.Option(False, "--include-deleted", help="Include deleted sources"),
    limit: int | None = typer.Option(None, "--limit", help="Maximum records"),
    offset: int = typer.Option(0, "--offset", help="Records to skip"),
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to use"),
    fmt: OutputFormat = typer.Option(OutputFormat.TABLE, "--format", "-f", case_sensitive=False),
) -> None:
    runtime = _context(profile)
    notebook_id = ensure_notebook_id(notebook, runtime.fallback_notebook())
    params = {
        "include_deleted": include_deleted,
        "limit": limit,
        "offset": offset,
    }
    if source_type:
        params["source_type"] = source_type
    if file_type:
        params["file_type"] = file_type
    with runtime.api_client() as client:
        response = client.get_json(f"/api/sources/notebook/{notebook_id}", params=params)
    runtime.remember_notebook(notebook_id)
    sources = response.get("sources", []) if isinstance(response, dict) else response
    for item in sources:
        item["tags"] = ", ".join(item.get("metadata", {}).get("tags", [])) if item.get("metadata") else ""
    render_output(sources, fmt=fmt, title=f"Sources for {notebook_id}")


@sources_app.command("show")
def show_source(
    source_id: str = typer.Argument(..., help="Source GUID"),
    include_deleted: bool = typer.Option(False, "--include-deleted", help="Include deleted sources"),
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to use"),
    fmt: OutputFormat = typer.Option(OutputFormat.TABLE, "--format", "-f", case_sensitive=False),
) -> None:
    runtime = _context(profile)
    with runtime.api_client() as client:
        response = client.get_json(f"/api/sources/{source_id}", params={"include_deleted": include_deleted})
    render_output(response, fmt=fmt, title=f"Source {source_id}")


@sources_app.command("remove")
def delete_source(
    source_id: str = typer.Argument(..., help="Source GUID"),
    notebook: str | None = typer.Option(None, "--notebook", "-n", help="Notebook GUID"),
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to use"),
) -> None:
    runtime = _context(profile)
    notebook_id = ensure_notebook_id(notebook, runtime.fallback_notebook())
    typer.confirm(f"Remove source {source_id}?", abort=True)
    with runtime.api_client() as client:
        client.delete(f"/api/sources/{source_id}", params={"notebook_id": notebook_id})
    console.print(f"[green]Source {source_id} removed.[/green]")

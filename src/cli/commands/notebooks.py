"""Notebook command group."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from ..output import OutputFormat, render_output, console
from ..runtime import RuntimeContext, load_runtime
from ..utils import comma_separated, ensure_notebook_id, read_json_payload

notebooks_app = typer.Typer(help="Manage notebooks.")
tags_app = typer.Typer(help="Add or remove notebook tags.")
notebooks_app.add_typer(tags_app, name="tags")


def _context(profile: str | None) -> RuntimeContext:
    return load_runtime(profile)


@notebooks_app.command("list")
def list_notebooks(
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to use"),
    limit: int | None = typer.Option(None, "--limit", help="Maximum records"),
    offset: int = typer.Option(0, "--offset", help="Records to skip"),
    tags: str | None = typer.Option(None, "--tags", help="Filter by comma-separated tags"),
    sort_by: str = typer.Option("updated_at", "--sort-by", help="Sort field"),
    sort_order: str = typer.Option("desc", "--sort-order", help="Sort order"),
    fmt: OutputFormat = typer.Option(OutputFormat.TABLE, "--format", "-f", case_sensitive=False),
) -> None:
    runtime = _context(profile)
    tag_list = comma_separated(tags)
    params = {
        "offset": offset,
        "sort_by": sort_by,
        "sort_order": sort_order,
    }
    if limit is not None:
        params["limit"] = limit
    if tag_list:
        params["tags"] = tag_list
    with runtime.api_client() as client:
        payload = client.get_json("/api/notebooks", params=params)
    notebooks = payload.get("notebooks", []) if isinstance(payload, dict) else []
    for notebook in notebooks:
        notebook["tags"] = ", ".join(notebook.get("tags") or [])
    render_output(
        notebooks,
        fmt=fmt,
        title=f"Notebooks (total: {payload.get('total', len(notebooks))})" if isinstance(payload, dict) else "Notebooks",
    )


@notebooks_app.command("create")
def create_notebook(
    name: str = typer.Option(None, "--name", prompt="Notebook name"),
    description: str | None = typer.Option(None, "--description", prompt=False),
    tags: str | None = typer.Option(None, "--tags", help="Comma-separated tags"),
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to use"),
    fmt: OutputFormat = typer.Option(OutputFormat.TABLE, "--format", "-f", case_sensitive=False),
) -> None:
    runtime = _context(profile)
    payload = {
        "name": name,
        "description": description,
        "tags": comma_separated(tags),
    }
    with runtime.api_client() as client:
        response = client.post_json("/api/notebooks", json=payload)
    notebook_id = response.get("id") if isinstance(response, dict) else None
    if notebook_id:
        runtime.remember_notebook(str(notebook_id))
    render_output(response, fmt=fmt, title="Notebook Created")


@notebooks_app.command("show")
def show_notebook(
    notebook_id: Optional[str] = typer.Argument(None, help="Notebook GUID"),
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to use"),
    include_sources: bool = typer.Option(False, "--include-sources", help="Fetch related sources"),
    fmt: OutputFormat = typer.Option(OutputFormat.TABLE, "--format", "-f", case_sensitive=False),
) -> None:
    runtime = _context(profile)
    resolved_id = ensure_notebook_id(notebook_id, runtime.recent_notebook())
    with runtime.api_client() as client:
        notebook = client.get_json(f"/api/notebooks/{resolved_id}")
        if include_sources:
            sources = client.get_json(f"/api/sources/notebook/{resolved_id}")
            notebook["sources"] = sources.get("sources", []) if isinstance(sources, dict) else sources
    runtime.remember_notebook(resolved_id)
    render_output(notebook, fmt=fmt, title=f"Notebook {resolved_id}")


@notebooks_app.command("update")
def update_notebook(
    notebook_id: Optional[str] = typer.Argument(None, help="Notebook GUID"),
    name: str | None = typer.Option(None, "--name", help="New name"),
    description: str | None = typer.Option(None, "--description", help="New description"),
    tags: str | None = typer.Option(None, "--tags", help="Replace tags (comma-separated)"),
    data_file: Path | None = typer.Option(None, "--data-file", help="JSON file with payload"),
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to use"),
    fmt: OutputFormat = typer.Option(OutputFormat.TABLE, "--format", "-f", case_sensitive=False),
) -> None:
    runtime = _context(profile)
    resolved_id = ensure_notebook_id(notebook_id, runtime.recent_notebook())
    payload = read_json_payload(data_file) if data_file else {}
    if name is not None:
        payload["name"] = name
    if description is not None:
        payload["description"] = description
    tag_list = comma_separated(tags)
    if tag_list is not None:
        payload["tags"] = tag_list
    if not payload:
        raise typer.BadParameter("No update fields supplied.")
    with runtime.api_client() as client:
        response = client.put_json(f"/api/notebooks/{resolved_id}", json=payload)
    runtime.remember_notebook(resolved_id)
    render_output(response, fmt=fmt, title="Notebook Updated")


@notebooks_app.command("rename")
def rename_notebook(
    notebook_id: Optional[str] = typer.Argument(None, help="Notebook GUID"),
    new_name: str = typer.Option(..., "--name", help="New name", prompt="New notebook name"),
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to use"),
    fmt: OutputFormat = typer.Option(OutputFormat.TABLE, "--format", "-f", case_sensitive=False),
) -> None:
    runtime = _context(profile)
    resolved_id = ensure_notebook_id(notebook_id, runtime.recent_notebook())
    payload = {"new_name": new_name}
    with runtime.api_client() as client:
        response = client.patch_json(f"/api/notebooks/{resolved_id}/rename", json=payload)
    runtime.remember_notebook(resolved_id)
    render_output(response, fmt=fmt, title="Notebook Renamed")


@tags_app.command("add")
def add_tags(
    notebook_id: Optional[str] = typer.Argument(None, help="Notebook GUID"),
    tags: str = typer.Option(..., "--tags", help="Tags to add (comma-separated)"),
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to use"),
    fmt: OutputFormat = typer.Option(OutputFormat.TABLE, "--format", "-f", case_sensitive=False),
) -> None:
    runtime = _context(profile)
    resolved_id = ensure_notebook_id(notebook_id, runtime.recent_notebook())
    tag_list = comma_separated(tags)
    if not tag_list:
        raise typer.BadParameter("Provide at least one tag.")
    with runtime.api_client() as client:
        response = client.post_json(f"/api/notebooks/{resolved_id}/tags", json={"tags": tag_list})
    runtime.remember_notebook(resolved_id)
    render_output(response, fmt=fmt, title="Tags Added")


@tags_app.command("remove")
def remove_tags(
    notebook_id: Optional[str] = typer.Argument(None, help="Notebook GUID"),
    tags: str = typer.Option(..., "--tags", help="Tags to remove (comma-separated)"),
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to use"),
    fmt: OutputFormat = typer.Option(OutputFormat.TABLE, "--format", "-f", case_sensitive=False),
) -> None:
    runtime = _context(profile)
    resolved_id = ensure_notebook_id(notebook_id, runtime.recent_notebook())
    tag_list = comma_separated(tags)
    if not tag_list:
        raise typer.BadParameter("Provide at least one tag.")
    with runtime.api_client() as client:
        response = client.request("DELETE", f"/api/notebooks/{resolved_id}/tags", json={"tags": tag_list})
        payload = response.json() if response.content else {}
    runtime.remember_notebook(resolved_id)
    render_output(payload, fmt=fmt, title="Tags Removed")


@notebooks_app.command("delete")
def delete_notebook(
    notebook_id: Optional[str] = typer.Argument(None, help="Notebook GUID"),
    cascade: bool = typer.Option(False, "--cascade", help="Delete related objects"),
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to use"),
) -> None:
    runtime = _context(profile)
    resolved_id = ensure_notebook_id(notebook_id, runtime.recent_notebook())
    typer.confirm(f"Delete notebook {resolved_id}?", abort=True)
    with runtime.api_client() as client:
        client.delete(f"/api/notebooks/{resolved_id}", params={"cascade": cascade})
    console.print(f"[green]Notebook {resolved_id} deleted.[/green]")


@notebooks_app.command("generate-blog-post")
def generate_blog_post(
    notebook_id: Optional[str] = typer.Argument(None, help="Notebook GUID"),
    title: str = typer.Option(..., "--title", prompt="Blog post title"),
    prompt_text: str | None = typer.Option(None, "--prompt", help="Custom prompt"),
    tone: str = typer.Option("informative", "--tone", help="Tone for the blog post"),
    include_references: bool = typer.Option(
        True,
        "--include-links/--no-include-links",
        help="Include reference links",
    ),
    target_word_count: int = typer.Option(550, "--word-count", help="Target word count"),
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to use"),
    fmt: OutputFormat = typer.Option(OutputFormat.TABLE, "--format", "-f", case_sensitive=False),
) -> None:
    runtime = _context(profile)
    resolved_id = ensure_notebook_id(notebook_id, runtime.recent_notebook())
    payload = {
        "title": title,
        "prompt": prompt_text,
        "tone": tone,
        "target_word_count": target_word_count,
        "include_references": include_references,
    }
    with runtime.api_client(timeout=120.0) as client:
        response = client.post_json(f"/api/notebooks/{resolved_id}/generate-blog-post", json=payload)
    runtime.remember_notebook(resolved_id)
    render_output(response, fmt=fmt, title="Blog Post Output")


@notebooks_app.command("recent")
def recent_notebook(
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to use"),
    set_id: str | None = typer.Option(None, "--set", help="Override recent notebook id"),
) -> None:
    runtime = _context(profile)
    if set_id:
        runtime.remember_notebook(set_id)
        console.print(f"[green]Recent notebook set to {set_id}.[/green]")
        return
    recent = runtime.recent_notebook()
    if recent:
        console.print(recent)
    else:
        console.print("No recent notebook tracked.")

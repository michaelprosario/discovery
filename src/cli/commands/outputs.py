"""Output-related CLI commands."""

from __future__ import annotations

from pathlib import Path

import typer

from ..output import OutputFormat, render_output, console
from ..runtime import RuntimeContext, load_runtime
from ..utils import ensure_notebook_id

outputs_app = typer.Typer(help="Manage generated outputs.")


def _context(profile: str | None) -> RuntimeContext:
    return load_runtime(profile)


@outputs_app.command("list")
def list_outputs(
    notebook: str | None = typer.Option(None, "--notebook", "-n", help="Notebook GUID"),
    output_type: str | None = typer.Option(None, "--type", help="Filter by output type"),
    status: str | None = typer.Option(None, "--status", help="Filter by status"),
    sort_by: str = typer.Option("updated_at", "--sort-by", help="Sort field"),
    sort_order: str = typer.Option("desc", "--sort-order", help="Sort order"),
    limit: int | None = typer.Option(None, "--limit", help="Maximum records"),
    offset: int = typer.Option(0, "--offset", help="Records to skip"),
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to use"),
    fmt: OutputFormat = typer.Option(OutputFormat.TABLE, "--format", "-f", case_sensitive=False),
) -> None:
    runtime = _context(profile)
    params = {
        "output_type": output_type,
        "status": status,
        "sort_by": sort_by,
        "sort_order": sort_order,
        "limit": limit,
        "offset": offset,
    }
    if notebook or runtime.recent_notebook():
        notebook_id = ensure_notebook_id(notebook, runtime.recent_notebook())
        params["notebook_id"] = notebook_id
        runtime.remember_notebook(notebook_id)
    with runtime.api_client() as client:
        response = client.get_json("/api/outputs", params=params)
    outputs = response.get("outputs", []) if isinstance(response, dict) else response
    render_output(outputs, fmt=fmt, title="Outputs")


@outputs_app.command("create")
def create_output(
    notebook: str | None = typer.Option(None, "--notebook", "-n", help="Notebook GUID"),
    title: str = typer.Option(..., "--title", prompt="Output title"),
    output_type: str = typer.Option("blog_post", "--type", help="Output type"),
    prompt_text: str | None = typer.Option(None, "--prompt", help="Custom prompt"),
    template: str | None = typer.Option(None, "--template", help="Template name"),
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to use"),
    fmt: OutputFormat = typer.Option(OutputFormat.TABLE, "--format", "-f", case_sensitive=False),
) -> None:
    runtime = _context(profile)
    notebook_id = ensure_notebook_id(notebook, runtime.recent_notebook())
    payload = {
        "title": title,
        "output_type": output_type,
        "prompt": prompt_text,
        "template_name": template,
    }
    with runtime.api_client(timeout=120.0) as client:
        response = client.post_json("/api/outputs", params={"notebook_id": notebook_id}, json=payload)
    runtime.remember_notebook(notebook_id)
    render_output(response, fmt=fmt, title="Output Created")


@outputs_app.command("show")
def show_output(
    output_id: str = typer.Argument(..., help="Output GUID"),
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to use"),
    fmt: OutputFormat = typer.Option(OutputFormat.TABLE, "--format", "-f", case_sensitive=False),
) -> None:
    runtime = _context(profile)
    with runtime.api_client() as client:
        response = client.get_json(f"/api/outputs/{output_id}")
    render_output(response, fmt=fmt, title=f"Output {output_id}")


@outputs_app.command("delete")
def delete_output(
    output_id: str = typer.Argument(..., help="Output GUID"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation"),
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to use"),
) -> None:
    runtime = _context(profile)
    if not force:
        typer.confirm(f"Delete output {output_id}?", abort=True)
    with runtime.api_client() as client:
        client.delete(f"/api/outputs/{output_id}")
    console.print(f"[green]Output {output_id} deleted.[/green]")


@outputs_app.command("preview")
def preview_output(
    output_id: str = typer.Argument(..., help="Output GUID"),
    length: int = typer.Option(300, "--length", help="Preview length"),
    out_path: Path | None = typer.Option(None, "--out", help="Write preview to file"),
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to use"),
) -> None:
    runtime = _context(profile)
    with runtime.api_client() as client:
        response = client.get_json(f"/api/outputs/{output_id}/preview", params={"length": length})
    preview = response.get("preview") if isinstance(response, dict) else None
    if out_path and preview is not None:
        out_path.write_text(preview, encoding="utf-8")
        console.print(f"[green]Preview written to {out_path}.[/green]")
    else:
        console.print(preview or "No preview available.")


@outputs_app.command("search")
def search_outputs(
    query: str = typer.Option(..., "--query", prompt="Search query"),
    notebook: str | None = typer.Option(None, "--notebook", "-n", help="Notebook GUID"),
    output_type: str | None = typer.Option(None, "--type", help="Filter by output type"),
    status: str | None = typer.Option(None, "--status", help="Filter by status"),
    sort_by: str = typer.Option("updated_at", "--sort-by", help="Sort field"),
    sort_order: str = typer.Option("desc", "--sort-order", help="Sort order"),
    limit: int | None = typer.Option(None, "--limit", help="Maximum records"),
    offset: int = typer.Option(0, "--offset", help="Records to skip"),
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to use"),
    fmt: OutputFormat = typer.Option(OutputFormat.TABLE, "--format", "-f", case_sensitive=False),
) -> None:
    runtime = _context(profile)
    params = {
        "q": query,
        "output_type": output_type,
        "status": status,
        "sort_by": sort_by,
        "sort_order": sort_order,
        "limit": limit,
        "offset": offset,
    }
    if notebook or runtime.recent_notebook():
        notebook_id = ensure_notebook_id(notebook, runtime.recent_notebook())
        params["notebook_id"] = notebook_id
        runtime.remember_notebook(notebook_id)
    with runtime.api_client() as client:
        response = client.get_json("/api/outputs/search", params=params)
    outputs = response.get("outputs", []) if isinstance(response, dict) else response
    render_output(outputs, fmt=fmt, title="Search Results")

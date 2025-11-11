"""Vector operations command group."""

from __future__ import annotations

import typer

from ..output import OutputFormat, render_output, console
from ..runtime import RuntimeContext, load_runtime
from ..utils import ensure_notebook_id

vectors_app = typer.Typer(help="Vector ingestion and search controls.")
collection_app = typer.Typer(help="Vector collection management.")
vectors_app.add_typer(collection_app, name="collection")


def _context(profile: str | None) -> RuntimeContext:
    return load_runtime(profile)


@vectors_app.command("ingest")
def ingest_notebook(
    notebook: str | None = typer.Option(None, "--notebook", "-n", help="Notebook GUID"),
    chunk_size: int = typer.Option(1000, "--chunk-size", help="Chunk size"),
    overlap: int = typer.Option(200, "--overlap", help="Chunk overlap"),
    force: bool = typer.Option(False, "--force", help="Force reingest"),
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to use"),
    fmt: OutputFormat = typer.Option(OutputFormat.TABLE, "--format", "-f", case_sensitive=False),
) -> None:
    runtime = _context(profile)
    notebook_id = ensure_notebook_id(notebook, runtime.fallback_notebook())
    payload = {"chunk_size": chunk_size, "overlap": overlap, "force_reingest": force}
    with runtime.api_client(timeout=300.0) as client:
        response = client.post_json(f"/api/notebooks/{notebook_id}/ingest", json=payload)
    runtime.remember_notebook(notebook_id)
    render_output(response, fmt=fmt, title="Ingestion Result")


@vectors_app.command("similar")
def similar_search(
    notebook: str | None = typer.Option(None, "--notebook", "-n", help="Notebook GUID"),
    query: str = typer.Option(..., "--query", prompt="Similarity query"),
    limit: int = typer.Option(10, "--limit", help="Maximum results"),
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to use"),
    fmt: OutputFormat = typer.Option(OutputFormat.TABLE, "--format", "-f", case_sensitive=False),
) -> None:
    runtime = _context(profile)
    notebook_id = ensure_notebook_id(notebook, runtime.fallback_notebook())
    params = {"query": query, "limit": limit}
    with runtime.api_client() as client:
        response = client.get_json(f"/api/notebooks/{notebook_id}/similar", params=params)
    runtime.remember_notebook(notebook_id)
    results = response.get("results", []) if isinstance(response, dict) else response
    render_output(results, fmt=fmt, title="Similarity Results")


@vectors_app.command("count")
def vector_count(
    notebook: str | None = typer.Option(None, "--notebook", "-n", help="Notebook GUID"),
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to use"),
    fmt: OutputFormat = typer.Option(OutputFormat.TABLE, "--format", "-f", case_sensitive=False),
) -> None:
    runtime = _context(profile)
    notebook_id = ensure_notebook_id(notebook, runtime.fallback_notebook())
    with runtime.api_client() as client:
        response = client.get_json(f"/api/notebooks/{notebook_id}/vectors/count")
    runtime.remember_notebook(notebook_id)
    render_output(response, fmt=fmt, title="Vector Count")


@vectors_app.command("purge")
def purge_vectors(
    notebook: str | None = typer.Option(None, "--notebook", "-n", help="Notebook GUID"),
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to use"),
) -> None:
    runtime = _context(profile)
    notebook_id = ensure_notebook_id(notebook, runtime.fallback_notebook())
    typer.confirm(f"Delete all vectors for notebook {notebook_id}?", abort=True)
    with runtime.api_client() as client:
        client.delete(f"/api/notebooks/{notebook_id}/vectors")
    console.print(f"[green]Vectors deleted for notebook {notebook_id}.[/green]")


@collection_app.command("create")
def create_collection(
    notebook: str | None = typer.Option(None, "--notebook", "-n", help="Notebook GUID"),
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to use"),
    fmt: OutputFormat = typer.Option(OutputFormat.TABLE, "--format", "-f", case_sensitive=False),
) -> None:
    runtime = _context(profile)
    notebook_id = ensure_notebook_id(notebook, runtime.fallback_notebook())
    with runtime.api_client() as client:
        response = client.post_json(f"/api/notebooks/{notebook_id}/collection", json={})
    runtime.remember_notebook(notebook_id)
    render_output(response, fmt=fmt, title="Collection Result")

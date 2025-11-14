"""Question answering commands."""

from __future__ import annotations

import typer

from ..output import OutputFormat, render_output, console
from ..runtime import RuntimeContext, load_runtime
from ..utils import ensure_notebook_id

qa_app = typer.Typer(help="Ask questions against notebooks.")


def _context(profile: str | None) -> RuntimeContext:
    return load_runtime(profile)


@qa_app.command("ask")
def ask_notebook(
    notebook: str | None = typer.Option(None, "--notebook", "-n", help="Notebook GUID"),
    question: str = typer.Option(..., "--question", prompt="Your question"),
    max_sources: int = typer.Option(5, "--max-sources", help="Source chunks to retrieve"),
    temperature: float = typer.Option(0.3, "--temperature", min=0.0, max=2.0, help="LLM temperature"),
    max_tokens: int = typer.Option(1500, "--max-tokens", help="Maximum tokens"),
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to use"),
    fmt: OutputFormat = typer.Option(OutputFormat.TEXT, "--format", "-f", case_sensitive=False),
) -> None:
    runtime = _context(profile)
    notebook_id = ensure_notebook_id(notebook, runtime.fallback_notebook())
    payload = {
        "question": question,
        "max_sources": max_sources,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    with runtime.api_client(timeout=120.0) as client:
        response = client.post_json(f"/api/notebooks/{notebook_id}/qa", json=payload)
    runtime.remember_notebook(notebook_id)
    if fmt == OutputFormat.TEXT:
        console.print(response.get("answer", ""))
        sources = response.get("sources", [])
        if sources:
            console.print("\n[b]Sources[/b]")
            for source in sources:
                name = source.get("source_name") or source.get("source_id")
                console.print(f"- {name}: score={source.get('relevance_score')}")
    else:
        render_output(response, fmt=fmt, title="QA Response")


@qa_app.command("health")
def qa_health(
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to use"),
    fmt: OutputFormat = typer.Option(OutputFormat.TABLE, "--format", "-f", case_sensitive=False),
) -> None:
    runtime = _context(profile)
    with runtime.api_client() as client:
        response = client.get_json("/api/notebooks/qa/health")
    render_output(response, fmt=fmt, title="QA Health")

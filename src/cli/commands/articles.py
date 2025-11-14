"""Article discovery command group."""

from __future__ import annotations

import typer

from ..output import OutputFormat, render_output
from ..runtime import RuntimeContext, load_runtime

articles_app = typer.Typer(help="Search external articles.")


def _context(profile: str | None) -> RuntimeContext:
    return load_runtime(profile)


@articles_app.command("search")
def search_articles(
    question: str = typer.Option(..., "--question", prompt="Search question"),
    limit: int = typer.Option(10, "--limit", help="Maximum articles"),
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to use"),
    fmt: OutputFormat = typer.Option(OutputFormat.TABLE, "--format", "-f", case_sensitive=False),
) -> None:
    runtime = _context(profile)
    payload = {"question": question, "max_results": limit}
    with runtime.api_client() as client:
        response = client.post_json("/articles/search", json=payload)
    articles = response.get("robust_articles", []) if isinstance(response, dict) else response
    render_output(articles, fmt=fmt, title="Articles")

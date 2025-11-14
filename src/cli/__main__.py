"""Entry point for the Discovery CLI."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

import typer

from .commands.articles import articles_app
from .commands.config import config_app
from .commands.notebooks import notebooks_app
from .commands.outputs import outputs_app
from .commands.qa import qa_app
from .commands.sources import sources_app
from .commands.vectors import vectors_app
from .output import console

app = typer.Typer(
    help="Interact with the Discovery research system via API.",
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
)


def _get_version() -> str:
    try:
        return version("discovery")
    except PackageNotFoundError:
        return "0.0.0"


@app.callback()
def main_callback(
    ctx: typer.Context,
    version_flag: bool = typer.Option(
        False, "--version", callback=None, is_eager=True, help="Show CLI version and exit"
    ),
) -> None:
    if version_flag:
        console.print(f"Discovery CLI {_get_version()}")
        raise typer.Exit()


app.add_typer(config_app, name="config", help="Configure API profiles.")
app.add_typer(notebooks_app, name="notebooks", help="Notebook management")
app.add_typer(notebooks_app, name="nb")
app.add_typer(sources_app, name="sources", help="Source ingestion")
app.add_typer(sources_app, name="src")
app.add_typer(vectors_app, name="vectors", help="Vector database operations")
app.add_typer(vectors_app, name="vec")
app.add_typer(outputs_app, name="outputs", help="Generated outputs")
app.add_typer(outputs_app, name="out")
app.add_typer(articles_app, name="articles", help="Article discovery")
app.add_typer(qa_app, name="qa", help="Question answering")

cli = typer.main.get_command(app)

if __name__ == "__main__":  # pragma: no cover - manual entry
    app()

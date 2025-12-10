"""Commands for managing Discovery CLI configuration."""

from __future__ import annotations

import typer

from ..config_store import ConfigStore, DiscoveryProfile
from ..http_client import DiscoveryApiClient
from ..output import OutputFormat, render_output, console
from ..runtime import load_runtime

config_app = typer.Typer(help="Configure Discovery CLI profiles.")


@config_app.command("init")
def init_config(
    url: str = typer.Option(None, "--url", prompt=False, help="Discovery API base URL"),
    api_key: str | None = typer.Option(None, "--api-key", help="API key for authentication"),
    profile: str = typer.Option("default", "--profile", "-p", help="Profile name"),
    default_notebook: str | None = typer.Option(None, "--default-notebook", help="Default notebook GUID"),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite existing configuration"),
) -> None:
    """Initialize a new CLI profile."""
    store = ConfigStore()
    if store.config_path.exists() and not overwrite:
        typer.confirm("Configuration already exists. Overwrite?", abort=True)
    if not url:
        url = typer.prompt("Discovery API URL", default="http://localhost:8000")
    
    profile_model = DiscoveryProfile(
        name=profile,
        url=url,
        api_key=api_key,
        default_notebook=default_notebook,
    )
    store.upsert_profile(profile_model, make_active=True)
    console.print(f"[green]Profile '{profile}' saved.[/green]")
    
    if api_key:
        console.print("[green]API key configured.[/green]")
    else:
        console.print("[yellow]No API key provided. Set one with: discovery auth set-api-key --key <your-key>[/yellow]")
    
    try:
        with DiscoveryApiClient(profile_model) as client:
            response = client.get_json("/health")
        console.print(f"[green]Connected successfully:[/green] {response}")
    except Exception as exc:  # pragma: no cover - depends on network
        console.print(f"[yellow]Warning:[/yellow] {exc}")


@config_app.command("show")
def show_config(raw: bool = typer.Option(False, "--raw", help="Emit machine-readable JSON")) -> None:
    store = ConfigStore()
    config = store.load()
    payload = config.model_dump(mode="json")
    if raw:
        render_output(payload, fmt=OutputFormat.JSON)
        return
    rows = []
    for name, profile in config.profiles.items():
        rows.append(
            {
                "profile": name,
                "url": profile.base_url,
                "api_key": "(set)" if profile.api_key else "",
                "default_notebook": profile.default_notebook or "",
                "active": "yes" if name == config.active_profile else "",
            }
        )
    render_output(rows, fmt=OutputFormat.TABLE, title="Configured Profiles")


@config_app.command("use")
def use_profile(name: str = typer.Argument(..., help="Profile to activate")) -> None:
    store = ConfigStore()
    store.set_active_profile(name)
    console.print(f"[green]Active profile set to '{name}'.[/green]")


@config_app.command("test")
def test_connection(
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to test"),
) -> None:
    runtime = load_runtime(profile)
    with DiscoveryApiClient(runtime.profile) as client:
        payload = client.get_json("/health")
    render_output(payload, fmt=OutputFormat.TABLE, title=f"Health @ {runtime.profile.base_url}")


@config_app.command("env")
def export_env(profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to export")) -> None:
    runtime = load_runtime(profile)
    profile_model = runtime.profile
    lines = [
        f"DISCOVERY_API_URL={profile_model.base_url}",
    ]
    if profile_model.api_key:
        lines.append(f"DISCOVERY_API_KEY={profile_model.api_key}")
    if profile_model.default_notebook:
        lines.append(f"DISCOVERY_NOTEBOOK_GUID={profile_model.default_notebook}")
    console.print("\n".join(lines))

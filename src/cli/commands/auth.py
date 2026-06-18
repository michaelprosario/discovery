"""Commands for managing authentication."""

from __future__ import annotations

import typer

from ..config_store import ConfigStore
from ..exceptions import ConfigNotInitializedError, DiscoveryCLIError
from ..http_client import DiscoveryApiClient
from ..output import console
from ..runtime import load_runtime

auth_app = typer.Typer(help="Manage authentication.")


def _save_profile(profile_obj) -> None:
    """Persist a profile back into the active config."""
    store = ConfigStore()
    config = store.load()
    config.set_profile(profile_obj)
    store.save(config)


@auth_app.command("register")
def register(
    email: str = typer.Option(..., "--email", "-e", help="Email to register"),
    password: str = typer.Option(
        ..., "--password", "-w", prompt=True, hide_input=True, confirmation_prompt=True,
        help="Password (min 8 chars)",
    ),
    display_name: str | None = typer.Option(None, "--name", "-n", help="Display name"),
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to use"),
) -> None:
    """Register a new user account on the backend."""
    try:
        runtime = load_runtime(profile)
        payload = {"email": email, "password": password}
        if display_name:
            payload["display_name"] = display_name
        with DiscoveryApiClient(runtime.profile) as client:
            user = client.post_json("/api/auth/register", json=payload)
        console.print(f"[green]✓ Registered '{user.get('email', email)}'[/green]")
        console.print("Run 'discovery auth login' to authenticate.")
    except ConfigNotInitializedError:
        console.print("[red]No profile configured.[/red] Run 'discovery config init' first.", style="bold")
        raise typer.Exit(1)
    except DiscoveryCLIError as exc:
        console.print(f"[red]Registration failed:[/red] {exc}", style="bold")
        raise typer.Exit(1)


@auth_app.command("login")
def login(
    email: str = typer.Option(..., "--email", "-e", help="Account email"),
    password: str = typer.Option(
        ..., "--password", "-w", prompt=True, hide_input=True, help="Account password",
    ),
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to update"),
) -> None:
    """Authenticate via OAuth2 password grant and store the JWT tokens."""
    try:
        runtime = load_runtime(profile)
        profile_obj = runtime.profile
        with DiscoveryApiClient(profile_obj) as client:
            # OAuth2 password grant expects form-encoded data.
            tokens = client.post_json(
                "/api/auth/token",
                data={"username": email, "password": password},
            )

        profile_obj.access_token = tokens.get("access_token")
        profile_obj.refresh_token = tokens.get("refresh_token")
        profile_obj.api_key = None  # supersede any legacy key
        _save_profile(profile_obj)

        console.print(f"[green]✓ Logged in as '{email}' (profile '{profile_obj.name}')[/green]")
    except ConfigNotInitializedError:
        console.print("[red]No profile configured.[/red] Run 'discovery config init' first.", style="bold")
        raise typer.Exit(1)
    except DiscoveryCLIError as exc:
        console.print(f"[red]Login failed:[/red] {exc}", style="bold")
        raise typer.Exit(1)


@auth_app.command("set-api-key")
def set_api_key(
    key: str = typer.Option(..., "--key", "-k", help="API key for authentication"),
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to update"),
) -> None:
    """Set a legacy static API key (prefer 'discovery auth login')."""
    try:
        runtime = load_runtime(profile)
        profile_obj = runtime.profile
        profile_obj.api_key = key
        _save_profile(profile_obj)
        console.print(f"[green]✓ API key set for profile '{profile_obj.name}'[/green]")
    except ConfigNotInitializedError:
        console.print(
            "[red]No profile configured.[/red] Run 'discovery config init' first.",
            style="bold",
        )
        raise typer.Exit(1)
    except DiscoveryCLIError as exc:
        console.print(f"[red]Failed to set API key:[/red] {exc}", style="bold")
        raise typer.Exit(1)


@auth_app.command("logout")
def logout(
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to logout"),
) -> None:
    """Revoke the refresh token (if any) and clear stored credentials."""
    try:
        runtime = load_runtime(profile)
        profile_obj = runtime.profile

        if not profile_obj.is_authenticated:
            console.print(f"[yellow]Profile '{profile_obj.name}' is not authenticated.[/yellow]")
            return

        # Best-effort server-side revocation of the refresh token.
        if profile_obj.refresh_token:
            try:
                with DiscoveryApiClient(profile_obj) as client:
                    client.request("POST", "/api/auth/logout", json={"refresh_token": profile_obj.refresh_token})
            except DiscoveryCLIError:
                pass  # token may already be expired/invalid; clear locally regardless

        profile_obj.access_token = None
        profile_obj.refresh_token = None
        profile_obj.api_key = None
        _save_profile(profile_obj)

        console.print(f"[green]✓ Logged out from profile '{profile_obj.name}'[/green]")
    except ConfigNotInitializedError:
        console.print("[red]No profile configured.[/red]", style="bold")
        raise typer.Exit(1)


@auth_app.command("status")
def auth_status(
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to check"),
) -> None:
    """Show current authentication status."""
    try:
        runtime = load_runtime(profile)
        profile_obj = runtime.profile

        console.print(f"[bold]Profile:[/bold] {profile_obj.name}")
        console.print(f"[bold]API URL:[/bold] {profile_obj.base_url}")

        if profile_obj.access_token:
            console.print(f"[bold]Auth Method:[/bold] JWT (Bearer token)")
            try:
                with DiscoveryApiClient(profile_obj) as client:
                    me = client.get_json("/api/auth/me")
                console.print(f"[bold]User:[/bold] {me.get('email')}")
                console.print(f"[bold]Roles:[/bold] {', '.join(me.get('roles', []))}")
                console.print(f"[bold]Status:[/bold] [green]Authenticated[/green]")
            except DiscoveryCLIError as exc:
                console.print(f"[bold]Status:[/bold] [yellow]Token present but not verified ({exc})[/yellow]")
        elif profile_obj.api_key:
            masked_key = f"{'*' * 8}{profile_obj.api_key[-4:]}" if len(profile_obj.api_key) > 4 else "****"
            console.print(f"[bold]Auth Method:[/bold] Legacy API Key")
            console.print(f"[bold]API Key:[/bold] {masked_key}")
            console.print(f"[bold]Status:[/bold] [green]Authenticated[/green]")
        else:
            console.print(f"[bold]Auth Method:[/bold] [red]Not authenticated[/red]")
            console.print("Run 'discovery auth login --email <you>' to authenticate.")
    except ConfigNotInitializedError:
        console.print("[red]No profile configured.[/red]", style="bold")
        raise typer.Exit(1)

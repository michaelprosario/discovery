"""Commands for managing authentication."""

from __future__ import annotations

import typer

from ..config_store import ConfigStore
from ..exceptions import ConfigNotInitializedError, DiscoveryCLIError
from ..http_client import DiscoveryApiClient
from ..output import console
from ..runtime import load_runtime

auth_app = typer.Typer(help="Manage authentication.")


@auth_app.command("set-api-key")
def set_api_key(
    key: str = typer.Option(..., "--key", "-k", help="API key for authentication"),
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to update"),
) -> None:
    """Set API key for authentication."""
    try:
        runtime = load_runtime(profile)
        profile_obj = runtime.profile
        
        # Update profile with API key
        profile_obj.api_key = key
        
        # Save updated profile
        store = ConfigStore()
        config = store.load()
        config.set_profile(profile_obj)
        store.save(config)
        
        console.print(f"[green]✓ API key set for profile '{profile_obj.name}'[/green]")
        
        # Verify connectivity with backend
        try:
            with DiscoveryApiClient(profile_obj) as api_client:
                response = api_client.get_json("/health")
                console.print(f"[green]✓ Connected to API successfully[/green]")
        except Exception as exc:
            console.print(f"[yellow]Warning: Could not verify API connection: {exc}[/yellow]")
            
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
    """Clear authentication credentials."""
    try:
        runtime = load_runtime(profile)
        profile_obj = runtime.profile
        
        if not profile_obj.api_key:
            console.print(f"[yellow]Profile '{profile_obj.name}' is not authenticated.[/yellow]")
            return
        
        # Clear credentials
        profile_obj.api_key = None
        
        # Save updated profile
        store = ConfigStore()
        config = store.load()
        config.set_profile(profile_obj)
        store.save(config)
        
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
        
        if profile_obj.api_key:
            # Mask API key, showing only last 4 characters
            masked_key = f"{'*' * 8}{profile_obj.api_key[-4:]}" if len(profile_obj.api_key) > 4 else "****"
            console.print(f"[bold]Auth Method:[/bold] API Key")
            console.print(f"[bold]API Key:[/bold] {masked_key}")
            console.print(f"[bold]Status:[/bold] [green]Authenticated[/green]")
        else:
            console.print(f"[bold]Auth Method:[/bold] [red]Not authenticated[/red]")
            console.print("Run 'discovery auth set-api-key --key <your-key>' to authenticate")
            
    except ConfigNotInitializedError:
        console.print("[red]No profile configured.[/red]", style="bold")
        raise typer.Exit(1)


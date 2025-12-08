"""Commands for managing authentication."""

from __future__ import annotations

from datetime import datetime, timezone

import typer

from ..config_store import ConfigStore
from ..exceptions import ConfigNotInitializedError, DiscoveryCLIError
from ..firebase_client import FirebaseAuthClient
from ..http_client import DiscoveryApiClient
from ..output import console
from ..runtime import load_runtime

auth_app = typer.Typer(help="Manage authentication.")


@auth_app.command("login")
def login_firebase(
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to authenticate"),
    device_flow: bool = typer.Option(False, "--device-flow", help="Use device flow for headless environments"),
) -> None:
    """Authenticate using Google Sign-In."""
    try:
        # Load the runtime to get the profile
        runtime = load_runtime(profile)
        profile_obj = runtime.profile
        
        # Initialize Firebase auth client
        client = FirebaseAuthClient()
        
        # Perform login
        credentials = client.login(use_device_flow=device_flow)
        
        # Update profile with new credentials
        profile_obj.firebase_credentials = credentials
        
        # Save updated profile
        store = ConfigStore()
        config = store.load()
        config.set_profile(profile_obj)
        store.save(config)
        
        console.print(f"[green]✓ Successfully authenticated profile '{profile_obj.name}'[/green]")
        
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
        console.print(f"[red]Authentication failed:[/red] {exc}", style="bold")
        raise typer.Exit(1)


@auth_app.command("logout")
def logout(
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to logout"),
) -> None:
    """Clear authentication credentials."""
    try:
        runtime = load_runtime(profile)
        profile_obj = runtime.profile
        
        if not profile_obj.firebase_credentials and not profile_obj.api_key:
            console.print(f"[yellow]Profile '{profile_obj.name}' is not authenticated.[/yellow]")
            return
        
        # Clear credentials
        profile_obj.firebase_credentials = None
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
        
        if profile_obj.firebase_credentials:
            creds = profile_obj.firebase_credentials
            console.print(f"[bold]Auth Method:[/bold] Firebase/Google")
            console.print(f"[bold]User Email:[/bold] {creds.user_email}")
            
            # Check token expiry
            now = datetime.now(timezone.utc)
            if creds.token_expiry > now:
                time_left = creds.token_expiry - now
                hours = int(time_left.total_seconds() // 3600)
                minutes = int((time_left.total_seconds() % 3600) // 60)
                console.print(f"[bold]Token Status:[/bold] [green]Valid[/green] (expires in {hours}h {minutes}m)")
            else:
                console.print(f"[bold]Token Status:[/bold] [yellow]Expired[/yellow] (will auto-refresh)")
                
        elif profile_obj.api_key:
            console.print(f"[bold]Auth Method:[/bold] [yellow]API Key (deprecated)[/yellow]")
            console.print(f"[bold]API Key:[/bold] {'*' * 8}{profile_obj.api_key[-4:]}")
            console.print("[yellow]Consider migrating to Firebase auth with 'discovery auth login'[/yellow]")
        else:
            console.print(f"[bold]Auth Method:[/bold] [red]Not authenticated[/red]")
            console.print("Run 'discovery auth login' to authenticate")
            
    except ConfigNotInitializedError:
        console.print("[red]No profile configured.[/red]", style="bold")
        raise typer.Exit(1)


@auth_app.command("refresh")
def refresh_token(
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to refresh"),
) -> None:
    """Manually refresh Firebase token."""
    try:
        runtime = load_runtime(profile)
        profile_obj = runtime.profile
        
        if not profile_obj.firebase_credentials:
            console.print(
                "[yellow]Profile is not authenticated with Firebase.[/yellow]\n"
                "Run 'discovery auth login' to authenticate."
            )
            raise typer.Exit(1)
        
        # Initialize Firebase client and refresh
        client = FirebaseAuthClient()
        new_credentials = client.refresh_token(profile_obj.firebase_credentials)
        
        # Update profile
        profile_obj.firebase_credentials = new_credentials
        
        # Save
        store = ConfigStore()
        config = store.load()
        config.set_profile(profile_obj)
        store.save(config)
        
        console.print(f"[green]✓ Token refreshed successfully[/green]")
        console.print(f"[bold]New expiry:[/bold] {new_credentials.token_expiry.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
    except ConfigNotInitializedError:
        console.print("[red]No profile configured.[/red]", style="bold")
        raise typer.Exit(1)
    except DiscoveryCLIError as exc:
        console.print(f"[red]Failed to refresh token:[/red] {exc}", style="bold")
        raise typer.Exit(1)

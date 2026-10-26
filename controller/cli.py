from pathlib import Path
import subprocess

from docker.errors import APIError, NotFound
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from controller.docker_controller import DockerController
from controller.nginx_manager import NginxManager


# --------------------------------------------------
# Dockloom configuration
# --------------------------------------------------

APP_NAME = "Dockloom"
APP_VERSION = "0.1.0"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGE_NAME = "local-container-app:1.0"

console = Console()

nginx_manager = NginxManager(
    config_path=PROJECT_ROOT / "nginx" / "upstreams.conf"
)


# --------------------------------------------------
# Branding and interface
# --------------------------------------------------

def print_header():
    logo = r"""
 ____             _    _
|  _ \  ___   ___| | _| | ___   ___  _ __ ___
| | | |/ _ \ / __| |/ / |/ _ \ / _ \| '_ ` _ \
| |_| | (_) | (__|   <| | (_) | (_) | | | | | |
|____/ \___/ \___|_|\_\_|\___/ \___/|_| |_| |_|
"""

    content = Text(logo, style="bold cyan")
    content.append(f"\n                 v{APP_VERSION}", style="bold white")
    content.append("\n       Build. Deploy. Balance.", style="italic bright_white")

    console.print(
        Panel(
            content,
            border_style="bright_blue",
            padding=(1, 2),
            expand=False,
        )
    )


def print_success(message):
    console.print(f"[bold green]✓[/bold green] {message}")


def print_error(message):
    console.print(f"[bold red]✗[/bold red] {message}")


def print_warning(message):
    console.print(f"[bold yellow]![/bold yellow] {message}")


def pause():
    console.input("\n[dim]Press Enter to continue...[/dim]")


# --------------------------------------------------
# Container management
# --------------------------------------------------

def list_containers(controller):
    containers = controller.list_containers()

    if not containers:
        console.print(
            Panel(
                "No managed containers found.",
                title="Containers",
                border_style="yellow",
            )
        )
        return

    table = Table(
        title="Managed Containers",
        border_style="bright_blue",
        header_style="bold cyan",
    )

    table.add_column("Name", style="white")
    table.add_column("ID", style="dim")
    table.add_column("Status")
    table.add_column("Host Port", justify="right")

    for container in containers:
        status = container["status"]

        status_style = (
            "green" if status == "running" else "red"
        )

        port = container.get("host_port")
        port_text = str(port) if port is not None else "-"

        table.add_row(
            container["name"],
            container["id"],
            f"[{status_style}]{status}[/{status_style}]",
            port_text,
        )

    console.print(table)


def sync_load_balancer(controller):
    """Synchronize Nginx with currently running replicas."""
    try:
        replicas = controller.list_running_replicas()
        nginx_manager.sync(replicas)

        print_success(
            f"Nginx synchronized with {len(replicas)} running replica(s)."
        )
        return True

    except (subprocess.CalledProcessError, OSError, ValueError) as error:
        print_warning("Container operation succeeded, but Nginx synchronization failed.")
        console.print(f"[dim]Details: {error}[/dim]")
        console.print(
            "Check the Nginx configuration before making further changes."
        )
        return False


def deploy_container(controller):
    console.print(
        Panel("Deploy an application", border_style="cyan")
    )

    replica_input = console.input("Replica count: ").strip()

    try:
        replica_count = int(replica_input)
    except ValueError:
        print_error("Replica count must be a number.")
        return

    if replica_count < 1:
        print_error("Replica count must be at least 1.")
        return

    start_port_input = console.input("Starting host port: ").strip()

    try:
        start_port = int(start_port_input)
    except ValueError:
        print_error("Starting port must be a number.")
        return

    end_port = start_port + replica_count - 1

    if start_port < 1024 or end_port > 65535:
        print_error("Replica ports must be between 1024 and 65535.")
        return

    try:
        results = controller.deploy_replicas(
            image=IMAGE_NAME,
            replica_count=replica_count,
            start_port=start_port,
        )

        print_success(f"{len(results)} replica(s) deployed.")

        table = Table(
            title="Deployment Results",
            border_style="green",
            header_style="bold cyan",
        )

        table.add_column("Container")
        table.add_column("Host Port", justify="right")
        table.add_column("Status")

        for result in results:
            table.add_row(
                result["name"],
                str(result["host_port"]),
                f"[green]{result['status']}[/green]",
            )

        console.print(table)
        sync_load_balancer(controller)

    except APIError as error:
        print_error("Could not deploy replicas.")
        console.print(
            f"[dim]{getattr(error, 'explanation', str(error))}[/dim]"
        )


def start_container(controller):
    console.print(Panel("Start a container", border_style="cyan"))
    name = console.input("Container name: ").strip()

    if not name:
        print_error("Container name cannot be empty.")
        return

    try:
        result = controller.start(name)
        print_success(f"{result['name']} started successfully.")
        sync_load_balancer(controller)

    except NotFound:
        print_error(f"Container '{name}' was not found.")

    except APIError as error:
        print_error("Could not start the container.")
        console.print(
            f"[dim]{getattr(error, 'explanation', str(error))}[/dim]"
        )


def stop_container(controller):
    console.print(Panel("Stop a container", border_style="cyan"))
    name = console.input("Container name: ").strip()

    if not name:
        print_error("Container name cannot be empty.")
        return

    try:
        result = controller.stop(name)
        print_success(f"{result['name']} stopped successfully.")
        sync_load_balancer(controller)

    except NotFound:
        print_error(f"Container '{name}' was not found.")

    except APIError as error:
        print_error("Could not stop the container.")
        console.print(
            f"[dim]{getattr(error, 'explanation', str(error))}[/dim]"
        )


def remove_container(controller):
    console.print(Panel("Remove a container", border_style="cyan"))
    name = console.input("Container name: ").strip()

    if not name:
        print_error("Container name cannot be empty.")
        return

    try:
        result = controller.remove(name)
        print_success(f"{result['name']} removed successfully.")
        sync_load_balancer(controller)

    except NotFound:
        print_error(f"Container '{name}' was not found.")

    except APIError as error:
        print_error("Container could not be removed.")
        console.print(
            f"[dim]{getattr(error, 'explanation', str(error))}[/dim]"
        )


# --------------------------------------------------
# Main menu
# --------------------------------------------------

def main():
    controller = DockerController()

    while True:
        console.clear()
        print_header()

        menu = Table(
            show_header=False,
            box=None,
            padding=(0, 2),
        )

        menu.add_column("Option", style="bold cyan", width=6)
        menu.add_column("Action", style="white")

        menu.add_row("1", "Deploy application")
        menu.add_row("2", "List containers")
        menu.add_row("3", "Start container")
        menu.add_row("4", "Stop container")
        menu.add_row("5", "Remove container")
        menu.add_row("6", "Exit")

        console.print(
            Panel(
                menu,
                title="[bold]MAIN MENU[/bold]",
                border_style="bright_blue",
                padding=(1, 2),
            )
        )

        choice = console.input(
            "\n[bold cyan]Select an option [1-6]: [/bold cyan]"
        ).strip()

        try:
            if choice == "1":
                deploy_container(controller)
            elif choice == "2":
                list_containers(controller)
            elif choice == "3":
                start_container(controller)
            elif choice == "4":
                stop_container(controller)
            elif choice == "5":
                remove_container(controller)
            elif choice == "6":
                console.print(
                    Panel(
                        "Thanks for using Dockloom. See you next time!",
                        border_style="bright_blue",
                    )
                )
                break
            else:
                print_error("Invalid choice. Please select 1-6.")

        except Exception as error:
            print_error(f"Unexpected error: {error}")

        pause()


if __name__ == "__main__":
    main()
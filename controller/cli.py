from pathlib import Path
import subprocess

from docker.errors import APIError, BuildError, NotFound
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from controller.docker_controller import DockerController
from controller.nginx_manager import NginxManager

import re
import json
import urllib.request
import urllib.error
from controller.repository_deployer import RepositoryDeployer
from collections import Counter
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

def check_container_health(controller):
    """Display the network health of running managed containers."""
    results = controller.check_health()

    if not results:
        console.print(
            Panel(
                "No running managed containers found.",
                title="Health Check",
                border_style="yellow",
            )
        )
        return

    table = Table(
        title="Container Health",
        border_style="bright_blue",
        header_style="bold cyan",
    )

    table.add_column("Name", style="white")
    table.add_column("Host Port", justify="right")
    table.add_column("Health")

    for container in results:
        health = container["health"]

        health_text = (
            "[green]HEALTHY[/green]"
            if health == "healthy"
            else "[red]UNHEALTHY[/red]"
        )

        table.add_row(
            container["name"],
            str(container["host_port"]),
            health_text,
        )

    console.print(table)


def deployment_dashboard(controller):
    """Display an overview of Dockloom's deployment state."""

    # Docker Engine status
    try:
        docker_running = controller.client.ping()
    except Exception:
        docker_running = False

    if not docker_running:
        console.print(
            Panel(
                "[red]Docker Engine is unavailable.[/red]\n"
                "Start Docker and try again.",
                title="Dockloom Deployment Dashboard",
                border_style="red",
            )
        )
        return

    # Managed container status
    containers = controller.list_containers()
    running_containers = [
        container for container in containers
        if container["status"] == "running"
    ]

    # Application HTTP health
    try:
        health_results = controller.check_health()
        health_by_name = {
            item["name"]: item["health"]
            for item in health_results
        }
    except Exception:
        health_by_name = {}

    healthy_count = sum(
        1 for health in health_by_name.values()
        if health == "healthy"
    )

    # Nginx service status
    nginx_active = (
        subprocess.run(
            ["systemctl", "is-active", "--quiet", "nginx"],
            check=False,
        ).returncode == 0
    )

    # Read the installed upstream configuration.
    upstream_ports = set()
    config_readable = False

    try:
        live_config = nginx_manager.live_config_path.read_text(
            encoding="utf-8"
        )
        config_readable = True

        for line in live_config.splitlines():
            match = re.search(
                r"server\s+127\.0\.0\.1:(\d+)([^;]*);",
                line,
            )
            if match and "down" not in match.group(2).split():
                upstream_ports.add(int(match.group(1)))

    except (OSError, ValueError):
        pass

    # Summary
    summary = Table.grid(padding=(0, 2))
    summary.add_column(style="bold white")
    summary.add_column()

    summary.add_row(
        "Docker Engine",
        "[green]Running[/green]",
    )
    summary.add_row(
        "Nginx Service",
        "[green]Active[/green]" if nginx_active
        else "[red]Inactive[/red]",
    )
    summary.add_row("Managed Containers", str(len(containers)))
    summary.add_row("Running Containers", str(len(running_containers)))
    summary.add_row(
        "Healthy Applications",
        f"{healthy_count}/{len(running_containers)}",
    )
    summary.add_row(
        "Configured Upstreams",
        str(len(upstream_ports)) if config_readable else "[yellow]Unknown[/yellow]",
    )

    console.print(
        Panel(
            summary,
            title="[bold cyan]DOCKLOOM PLATFORM STATUS[/bold cyan]",
            border_style="bright_blue",
            padding=(1, 2),
        )
    )

    # Running container details
    if not running_containers:
        console.print(
            Panel(
                "No running managed containers.",
                title="Active Backends",
                border_style="yellow",
            )
        )
        return

    table = Table(
        title="ACTIVE BACKENDS",
        border_style="bright_blue",
        header_style="bold cyan",
    )

    table.add_column("Container", style="white")
    table.add_column("Host Port", justify="right")
    table.add_column("Health")
    table.add_column("Nginx Upstream")

    for container in running_containers:
        name = container["name"]
        port = container.get("host_port")
        health = health_by_name.get(name, "unknown")

        if health == "healthy":
            health_text = "[green]HEALTHY[/green]"
        elif health == "unhealthy":
            health_text = "[red]UNHEALTHY[/red]"
        else:
            health_text = "[yellow]UNKNOWN[/yellow]"

        is_upstream = port is not None and port in upstream_ports

        upstream_text = (
            "[green]Configured[/green]"
            if is_upstream
            else "[yellow]Not configured[/yellow]"
        )

        table.add_row(
            name,
            str(port) if port is not None else "-",
            health_text,
            upstream_text,
        )

    console.print(table)


def load_balancing_dashboard(request_count=12):
    """Send requests through Nginx and display backend distribution."""
    url = "http://127.0.0.1:8080"

    backend_counts = Counter()
    backend_samples = {}
    failures = 0

    console.print(
        Panel(
            f"Sending {request_count} requests through Nginx...",
            title="Dockloom Load Balancing",
            border_style="cyan",
        )
    )

    for _ in range(request_count):
        try:
            with urllib.request.urlopen(url, timeout=3) as response:
                body = response.read().decode("utf-8", errors="replace")

                try:
                    data = json.loads(body)
                    backend = data.get("container", "Unknown backend")
                except json.JSONDecodeError:
                    backend = "Other backend (non-JSON)"

                backend_counts[backend] += 1
                backend_samples.setdefault(backend, body.strip()[:60])

        except (urllib.error.URLError, TimeoutError, OSError):
            failures += 1

    table = Table(title="Request Distribution", show_lines=True)
    table.add_column("Backend", style="cyan")
    table.add_column("Requests", justify="right")
    table.add_column("Distribution", justify="right")
    table.add_column("Sample Response")

    for backend, count in sorted(backend_counts.items()):
        percentage = (count / request_count) * 100
        table.add_row(
            backend,
            str(count),
            f"{percentage:.1f}%",
            backend_samples[backend],
        )

    console.print(table)

    console.print(
        f"\n[green]Successful requests:[/green] "
        f"{request_count - failures}/{request_count}"
    )
    console.print(f"[red]Failed requests:[/red] {failures}")

    if len(backend_counts) > 1:
        console.print(
            "\n[green]Multiple backends handled requests.[/green]"
        )
    elif backend_counts:
        console.print(
            "\n[yellow]Only one backend handled successful requests.[/yellow]"
        )


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


def deploy_repository(controller):
    """Clone a GitHub repository, build its image, and deploy replicas."""
    console.print(
        Panel(
            "Deploy a GitHub repository\n\n"
            "[yellow]Note:[/yellow] The repository must contain a "
            "Dockerfile in its root directory.",
            border_style="cyan",
        )
    )

    repository_url = console.input("GitHub repository URL: ").strip()

    if not repository_url:
        print_error("Repository URL cannot be empty.")
        return

    try:
        replica_count = int(
            console.input("Replica count: ").strip()
        )
        if replica_count < 1:
            print_error("Replica count must be at least 1.")
            return

        container_port = int(
            console.input("Internal container port: ").strip()
        )
        if not 1 <= container_port <= 65535:
            print_error("Container port must be between 1 and 65535.")
            return

        start_port = int(
            console.input("Starting host port: ").strip()
        )

    except ValueError:
        print_error("Replica count and ports must be valid numbers.")
        return

    end_port = start_port + replica_count - 1

    if start_port < 1024 or end_port > 65535:
        print_error("Host ports must be between 1024 and 65535.")
        return

    deployer = RepositoryDeployer()
    repository_path = None

    try:
        owner, repository = deployer.validate_url(repository_url)

        # Keep image names and container prefixes Docker-compatible.
        repository_key = re.sub(
            r"[^a-z0-9_.-]+",
            "-",
            f"{owner}-{repository}".lower(),
        ).strip("-.")

        image_name = f"dockloom-{repository_key}:latest"
        name_prefix = f"lcp-app-{repository_key}"

        console.print("\n[cyan]Cloning repository...[/cyan]")
        repository_path = deployer.clone_repository(repository_url)

        console.print("[cyan]Building Docker image...[/cyan]")
        deployer.build_image(
            repository_path=repository_path,
            image_name=image_name,
            docker_client=controller.client,
        )

        console.print("[cyan]Deploying replicas...[/cyan]")
        results = controller.deploy_replicas(
            image=image_name,
            replica_count=replica_count,
            start_port=start_port,
            container_port=container_port,
            name_prefix=name_prefix,
        )

        print_success(
            f"Deployed {len(results)} replica(s) from {owner}/{repository}."
        )

        table = Table(
            title="Repository Deployment Results",
            border_style="green",
            header_style="bold cyan",
        )
        table.add_column("Container")
        table.add_column("Host Port", justify="right")
        table.add_column("Container Port", justify="right")
        table.add_column("Status")

        for result in results:
            table.add_row(
                result["name"],
                str(result["host_port"]),
                str(result["container_port"]),
                f"[green]{result['status']}[/green]",
            )

        console.print(table)
        sync_load_balancer(controller)

    except (
        ValueError,
        FileExistsError,
        RuntimeError,
        BuildError,
        APIError,
        OSError,
    ) as error:
        print_error("Repository deployment failed.")
        console.print(f"[dim]{error}[/dim]")


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

        menu.add_row("1", "Deploy demo application")
        menu.add_row("2", "Deploy GitHub repository")
        menu.add_row("3", "List containers")
        menu.add_row("4", "Start container")
        menu.add_row("5", "Stop container")
        menu.add_row("6", "Remove container")
        menu.add_row("7", "Check container health")
        menu.add_row("8", "Deployment Dashboard")
        menu.add_row("9", "Load Balancing Dashboard")
        menu.add_row("10", "Exit")  

        console.print(
            Panel(
                menu,
                title="[bold]MAIN MENU[/bold]",
                border_style="bright_blue",
                padding=(1, 2),
            )
        )

        choice = console.input(
            "\n[bold cyan]Select an option [1-9]: [/bold cyan]"
        ).strip()

        try:
            if choice == "1":
                deploy_container(controller)
            elif choice == "2":
                deploy_repository(controller)
            elif choice == "3":
                list_containers(controller)
            elif choice == "4":
                start_container(controller)
            elif choice == "5":
                stop_container(controller)
            elif choice == "6":
                remove_container(controller)
            elif choice == "7":
                check_container_health(controller)
            elif choice == "8":
                deployment_dashboard(controller)
            elif choice == "9":
                load_balancing_dashboard()
            elif choice == "10":
                console.print(
                    Panel(
                        "Thanks for using Dockloom. See you next time!",
                        border_style="bright_blue",
                    )
                )
                break   
            else:
                print_error("Invalid choice. Please select 1-9.")

        except Exception as error:
            print_error(f"Unexpected error: {error}")

        pause()


if __name__ == "__main__":
    main()
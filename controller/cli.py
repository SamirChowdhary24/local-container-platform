from docker.errors import APIError, NotFound

from controller.docker_controller import DockerController


IMAGE_NAME = "local-container-app:1.0"


def print_header():
    print("\n" + "=" * 45)
    print("     Local Container Service Platform")
    print("=" * 45)


def list_containers(controller):
    containers = controller.list_containers()

    if not containers:
        print("\nNo managed containers found.")
        return

    print("\nManaged Containers:")
    print("-" * 65)
    print(f"{'Name':<18}{'ID':<15}{'Status':<12}")
    print("-" * 65)

    for container in containers:
        print(
            f"{container['name']:<18}"
            f"{container['id']:<15}"
            f"{container['status']:<12}"
        )


def deploy_container(controller):
    print("\n--- Deploy Container ---")

    name = input("Container name: ").strip()

    if not name:
        print("Error: Container name cannot be empty.")
        return

    if not name.startswith("lcp-app-"):
        print("Error: Container name must start with 'lcp-app-'.")
        return

    port_input = input("Host port: ").strip()

    try:
        host_port = int(port_input)
    except ValueError:
        print("Error: Port must be a number.")
        return

    if not 1024 <= host_port <= 65535:
        print("Error: Port must be between 1024 and 65535.")
        return

    try:
        result = controller.deploy(
            name=name,
            image=IMAGE_NAME,
            host_port=host_port,
        )

        print("\n✓ Container deployed successfully.")
        print(f"  Name:   {result['name']}")
        print(f"  ID:     {result['id']}")
        print(f"  Status: {result['status']}")
        print(f"  Port:   {result['host_port']}")

    except APIError as error:
        print(f"\nError: Could not deploy container.")
        print(f"Details: {error.explanation}")


def start_container(controller):
    print("\n--- Start Container ---")

    name = input("Container name: ").strip()

    if not name:
        print("Error: Container name cannot be empty.")
        return

    try:
        result = controller.start(name)
        print(f"\n✓ {result['name']} started successfully.")

    except NotFound:
        print(f"\nError: Container '{name}' was not found.")

    except APIError as error:
        print(f"\nError: Could not start container.")
        print(f"Details: {error.explanation}")


def stop_container(controller):
    print("\n--- Stop Container ---")

    name = input("Container name: ").strip()

    if not name:
        print("Error: Container name cannot be empty.")
        return

    try:
        result = controller.stop(name)
        print(f"\n✓ {result['name']} stopped successfully.")

    except NotFound:
        print(f"\nError: Container '{name}' was not found.")

    except APIError as error:
        print(f"\nError: Could not stop container.")
        print(f"Details: {error.explanation}")


def remove_container(controller):
    print("\n--- Remove Container ---")

    name = input("Container name: ").strip()

    if not name:
        print("Error: Container name cannot be empty.")
        return

    try:
        result = controller.remove(name)
        print(f"\n✓ {result['name']} removed successfully.")

    except NotFound:
        print(f"\nError: Container '{name}' was not found.")

    except APIError as error:
        print("\nError: Container could not be removed.")
        print("Make sure the container is stopped before removing it.")


def main():
    controller = DockerController()

    while True:
        print_header()

        print("1. Deploy container")
        print("2. List containers")
        print("3. Start container")
        print("4. Stop container")
        print("5. Remove container")
        print("6. Exit")

        choice = input("\nEnter choice: ").strip()

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
                print("\nExiting Local Container Service Platform.")
                break

            else:
                print("\nError: Invalid choice. Please select 1-6.")

        except Exception as error:
            print(f"\nUnexpected error: {error}")

        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
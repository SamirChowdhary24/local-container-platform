
import docker


class DockerController:
    def __init__(self, client=None):
        self.client = client or docker.from_env()

    def deploy(self, name, image, host_port, container_port=8000):
        """Create and start a container."""
        container = self.client.containers.run(
            image=image,
            name=name,
            ports={f"{container_port}/tcp": host_port},
            environment={"CONTAINER_NAME": name},
            detach=True,
        )

        return {
            "id": container.short_id,
            "name": container.name,
            "status": "running",
            "host_port": host_port,
            "container_port": container_port,
        }

    def deploy_replicas(
        self, image, replica_count, start_port, container_port=8000, name_prefix="lcp-app",
    ):
        """Create multiple replicas using unused container names."""
        existing = self.list_containers()
        used_numbers = set()

        for container in existing:
            name = container["name"]
            prefix = f"{name_prefix}-"

            if name.startswith(prefix):
                suffix = name.removeprefix(prefix)
                if suffix.isdigit():
                    used_numbers.add(int(suffix))

        replicas = []
        number = 1

        while len(replicas) < replica_count:
            if number not in used_numbers:
                host_port = start_port + len(replicas)

                replica = self.deploy(
                    name=f"{name_prefix}-{number}",
                    image=image,
                    host_port=host_port,
                    container_port=container_port,
                )

                replicas.append(replica)
                used_numbers.add(number)

            number += 1

        return replicas

    def list_containers(self):
        """List managed containers, including stopped containers."""
        containers = self.client.containers.list(
            all=True,
            filters={"name": "lcp-app-"},
        )

        results = []

        for container in containers:
            host_port = None

            try:
                port_mappings = container.attrs["NetworkSettings"]["Ports"]

                # Find the first published port, regardless of container port.
                for mappings in port_mappings.values():
                    if mappings:
                        host_port = int(mappings[0]["HostPort"])
                        break

            except (KeyError, IndexError, TypeError, ValueError):
                pass

            results.append({
                "id": container.short_id,
                "name": container.name,
                "status": container.status,
                "host_port": host_port,
            })

        return results

    def list_running_replicas(self):
        """Return running replicas with known host ports for Nginx."""
        return [
            container
            for container in self.list_containers()
            if container["status"] == "running"
            and container["host_port"] is not None
        ]

    def start(self, name):
        """Start a stopped container."""
        container = self.client.containers.get(name)
        container.start()
        return {"name": container.name, "status": "started"}

    def stop(self, name):
        """Stop a running container."""
        container = self.client.containers.get(name)
        container.stop()
        return {"name": container.name, "status": "stopped"}

    def remove(self, name):
        """Remove a container."""
        container = self.client.containers.get(name)
        container.remove()
        return {"name": name, "status": "removed"}

import docker


class DockerController:
    def __init__(self, client=None):
        self.client = client or docker.from_env()

    def deploy(self, name, image, host_port):
        """Create and start a container."""
        container = self.client.containers.run(
            image=image,
            name=name,
            ports={"8000/tcp": host_port},
            detach=True,
        )

        return {
            "id": container.short_id,
            "name": container.name,
            "status": container.status,
            "host_port": host_port,
        }

    def list_containers(self):
        """List containers managed by this platform."""
        containers = self.client.containers.list(
            all=True,
            filters={"name": "lcp-app-"},
        )

        return [
            {
                "id": container.short_id,
                "name": container.name,
                "status": container.status,
            }
            for container in containers
        ]

    def start(self, name):
        """Start a stopped container."""
        container = self.client.containers.get(name)
        container.start()

        return {
            "name": container.name,
            "status": "started",
        }

    def stop(self, name):
        """Stop a running container."""
        container = self.client.containers.get(name)
        container.stop()

        return {
            "name": container.name,
            "status": "stopped",
        }

    def remove(self, name):
        """Remove a stopped container."""
        container = self.client.containers.get(name)
        container.remove()

        return {
            "name": name,
            "status": "removed",
        }

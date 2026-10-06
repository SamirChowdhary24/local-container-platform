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
            environment={
                "CONTAINER_NAME": name,
            },
            detach=True,
        )

        return {
            "id": container.short_id,
            "name": container.name,
            "status": "running",
            "host_port": host_port,
        }

    def deploy_replicas(self, image, replica_count, start_port):
        """Create and start multiple application replicas."""
        existing_containers = self.list_containers()

        used_numbers = set()

        for container in existing_containers:
            name = container["name"]

            if name.startswith("lcp-app-"):
                try:
                    number = int(name.replace("lcp-app-", ""))
                    used_numbers.add(number)
                except ValueError:
                    continue

        next_number = 1

        while next_number in used_numbers:
            next_number += 1

        replicas = []

        for index in range(replica_count):
            name = f"lcp-app-{next_number + index}"
            host_port = start_port + index

            replica = self.deploy(
                name=name,
                image=image,
                host_port=host_port,
            )

            replicas.append(replica)

        return replicas

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
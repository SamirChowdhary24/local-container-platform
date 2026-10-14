
import os
import subprocess
import tempfile
from pathlib import Path


class NginxManager:
    def __init__(
        self,
        config_path,
        live_config_path="/etc/nginx/local-container-platform-upstreams.conf",
    ):
        self.config_path = Path(config_path).resolve()
        self.live_config_path = Path(live_config_path)

    def generate_upstream(self, replicas):
        """Generate an upstream block from running replicas."""
        lines = [
            "upstream local_container_backend {",
            "    zone local_container_backend 64k;",
        ]

        if replicas:
            for replica in replicas:
                host_port = int(replica["host_port"])

                if not 1 <= host_port <= 65535:
                    raise ValueError(f"Invalid host port: {host_port}")

                lines.append(
                    f"    server 127.0.0.1:{host_port};"
                )
        else:
            # Valid configuration when no replicas are running.
            lines.append("    server 127.0.0.1:9 down;")

        lines.append("}")
        return "\n".join(lines)

    def write_config(self, replicas):
        """Write the project-owned upstream file atomically."""
        config = self.generate_upstream(replicas)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        temp_path = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.config_path.parent,
                delete=False,
            ) as temp_file:
                temp_file.write(config + "\n")
                temp_path = temp_file.name

            os.replace(temp_path, self.config_path)
        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)

        return config

    def sync(self, replicas):
        """Install the generated config, validate Nginx, and reload."""
        self.write_config(replicas)

        subprocess.run(
            [
                "sudo",
                "install",
                "-m",
                "644",
                str(self.config_path),
                str(self.live_config_path),
            ],
            check=True,
        )

        subprocess.run(
            ["sudo", "nginx", "-t"],
            check=True,
        )

        subprocess.run(
            ["sudo", "systemctl", "reload", "nginx"],
            check=True,
        )

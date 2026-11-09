
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPOSITORY_WORKSPACE = PROJECT_ROOT / "workspace" / "repositories"


class RepositoryDeployer:
    """Clone and validate GitHub repositories for Docker deployment."""

    def validate_url(self, repository_url):
        """Accept standard HTTPS GitHub repository URLs."""
        parsed_url = urlparse(repository_url.strip())

        if (
            parsed_url.scheme != "https"
            or parsed_url.netloc != "github.com"
            or parsed_url.query
            or parsed_url.fragment
        ):
            raise ValueError(
                "Please provide a valid HTTPS GitHub repository URL."
            )

        path_parts = parsed_url.path.strip("/").split("/")

        if (
            len(path_parts) != 2
            or not all(path_parts)
            or not all(
                re.fullmatch(r"[A-Za-z0-9_.-]+", part)
                for part in path_parts
            )
        ):
            raise ValueError(
                "Expected a repository URL like "
                "https://github.com/owner/repository"
            )

        owner, repository = path_parts
        repository = repository.removesuffix(".git")

        if not owner or not repository:
            raise ValueError("GitHub owner and repository name are required.")

        return owner, repository

    def clone_repository(self, repository_url):
        """Clone a repository into Dockloom's workspace."""
        owner, repository = self.validate_url(repository_url)

        REPOSITORY_WORKSPACE.mkdir(parents=True, exist_ok=True)

        destination = REPOSITORY_WORKSPACE / f"{owner}-{repository}"

        if destination.exists():
            raise FileExistsError(
                f"Repository destination already exists: {destination}"
            )

        normalized_url = (
            f"https://github.com/{owner}/{repository}.git"
        )

        try:
            subprocess.run(
                ["git", "clone", "--", normalized_url, str(destination)],
                check=True,
                capture_output=True,
                text=True,
                timeout=120,
            )
        except subprocess.CalledProcessError as error:
            message = error.stderr.strip() or "Git clone failed."
            raise RuntimeError(message) from error
        except subprocess.TimeoutExpired as error:
            raise RuntimeError("Repository cloning timed out.") from error

        if not (destination / "Dockerfile").is_file():
            raise ValueError(
                "No Dockerfile found in this repository."
            )

        return destination

    
    def build_image(self, repository_path, image_name, docker_client):
        """Build a Docker image from a repository's Dockerfile."""
        image, _ = docker_client.images.build(
            path=str(repository_path),
            tag=image_name,
        )
        return image

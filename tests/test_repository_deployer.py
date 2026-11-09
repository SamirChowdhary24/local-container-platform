
import pytest
from unittest.mock import MagicMock
from controller.repository_deployer import RepositoryDeployer
from unittest.mock import patch
from pathlib import Path

@pytest.fixture
def deployer():
    return RepositoryDeployer()


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (
            "https://github.com/fastapi/fastapi",
            ("fastapi", "fastapi"),
        ),
        (
            "https://github.com/pallets/flask.git",
            ("pallets", "flask"),
        ),
    ],
)
def test_validate_url_accepts_valid_github_urls(deployer, url, expected):
    assert deployer.validate_url(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "",
        "not-a-url",
        "http://github.com/owner/repo",
        "https://example.com/owner/repo",
        "https://github.com/owner",
        "https://github.com/owner/repo/extra",
        "https://github.com/owner/repo?query=test",
        "https://github.com.evil.com/owner/repo",
    ],
)
def test_validate_url_rejects_invalid_urls(deployer, url):
    with pytest.raises(ValueError):
        deployer.validate_url(url)


def test_clone_repository_success(deployer, tmp_path):
    destination = tmp_path / "fastapi-fastapi"

    def fake_clone(command, **kwargs):
        clone_path = Path(command[-1])
        clone_path.mkdir(parents=True)
        (clone_path / "Dockerfile").write_text(
            "FROM python:3.12-slim\n"
        )

    with (
        patch(
            "controller.repository_deployer.REPOSITORY_WORKSPACE",
            tmp_path,
        ),
        patch(
            "controller.repository_deployer.subprocess.run",
            side_effect=fake_clone,
        ) as mock_run,
    ):
        result = deployer.clone_repository(
            "https://github.com/fastapi/fastapi"
        )

    assert result == destination
    assert (result / "Dockerfile").is_file()
    mock_run.assert_called_once()


def test_clone_repository_without_dockerfile(deployer, tmp_path):
    def fake_clone(command, **kwargs):
        Path(command[-1]).mkdir(parents=True)

    with (
        patch(
            "controller.repository_deployer.REPOSITORY_WORKSPACE",
            tmp_path,
        ),
        patch(
            "controller.repository_deployer.subprocess.run",
            side_effect=fake_clone,
        ),
    ):
        with pytest.raises(ValueError, match="No Dockerfile found"):
            deployer.clone_repository(
                "https://github.com/fastapi/fastapi"
            )


def test_clone_repository_existing_destination(deployer, tmp_path):
    destination = tmp_path / "fastapi-fastapi"
    destination.mkdir()

    with (
        patch(
            "controller.repository_deployer.REPOSITORY_WORKSPACE",
            tmp_path,
        ),
        patch(
            "controller.repository_deployer.subprocess.run",
        ) as mock_run,
    ):
        with pytest.raises(FileExistsError):
            deployer.clone_repository(
                "https://github.com/fastapi/fastapi"
            )

    mock_run.assert_not_called()


def test_clone_repository_git_failure(deployer, tmp_path):
    import subprocess

    with (
        patch(
            "controller.repository_deployer.REPOSITORY_WORKSPACE",
            tmp_path,
        ),
        patch(
            "controller.repository_deployer.subprocess.run",
            side_effect=subprocess.CalledProcessError(
                128,
                ["git", "clone"],
                stderr="Repository not found",
            ),
        ),
    ):
        with pytest.raises(RuntimeError, match="Repository not found"):
            deployer.clone_repository(
                "https://github.com/fastapi/fastapi"
            )


def test_build_image(deployer, tmp_path):
    docker_client = MagicMock()
    expected_image = MagicMock()
    docker_client.images.build.return_value = (expected_image, [])

    result = deployer.build_image(
        repository_path=tmp_path,
        image_name="dockloom-fastapi:latest",
        docker_client=docker_client,
    )

    assert result is expected_image
    docker_client.images.build.assert_called_once_with(
        path=str(tmp_path),
        tag="dockloom-fastapi:latest",
    )

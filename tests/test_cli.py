from unittest.mock import MagicMock, patch

from docker.errors import BuildError

from controller import cli


def run_repository_deployment(inputs):
    """Run deploy_repository with mocked user input."""
    with patch.object(cli.console, "input", side_effect=inputs):
        cli.deploy_repository(MagicMock())


def test_deploy_repository_rejects_empty_url():
    with patch.object(cli, "print_error") as error:
        run_repository_deployment([""])

    error.assert_called_once_with("Repository URL cannot be empty.")


def test_deploy_repository_rejects_invalid_replica_count():
    with patch.object(cli, "print_error") as error:
        run_repository_deployment([
            "https://github.com/example/demo",
            "abc",
        ])

    error.assert_called_once_with(
        "Replica count and ports must be valid numbers."
    )


def test_deploy_repository_rejects_zero_replicas():
    with patch.object(cli, "print_error") as error:
        run_repository_deployment([
            "https://github.com/example/demo",
            "0",
        ])

    error.assert_called_once_with(
        "Replica count must be at least 1."
    )


def test_deploy_repository_rejects_invalid_container_port():
    with patch.object(cli, "print_error") as error:
        run_repository_deployment([
            "https://github.com/example/demo",
            "2",
            "70000",
        ])

    error.assert_called_once_with(
        "Container port must be between 1 and 65535."
    )


def test_deploy_repository_rejects_invalid_host_port():
    with patch.object(cli, "print_error") as error:
        run_repository_deployment([
            "https://github.com/example/demo",
            "2",
            "8000",
            "65535",
        ])

    error.assert_called_once_with(
        "Host ports must be between 1024 and 65535."
    )


@patch.object(cli, "sync_load_balancer")
@patch.object(cli, "RepositoryDeployer")
def test_deploy_repository_success(mock_deployer_class, mock_sync):
    controller = MagicMock()
    deployer = mock_deployer_class.return_value

    deployer.validate_url.return_value = ("example", "demo")
    deployer.clone_repository.return_value = "/tmp/example-demo"

    controller.deploy_replicas.return_value = [
        {
            "name": "lcp-app-example-demo-1",
            "host_port": 8080,
            "container_port": 8000,
            "status": "running",
        },
        {
            "name": "lcp-app-example-demo-2",
            "host_port": 8081,
            "container_port": 8000,
            "status": "running",
        },
    ]

    inputs = [
        "https://github.com/example/demo",
        "2",
        "8000",
        "8080",
    ]

    with (
        patch.object(cli.console, "input", side_effect=inputs),
        patch.object(cli, "print_success") as success,
    ):
        cli.deploy_repository(controller)

    deployer.validate_url.assert_called_once_with(
        "https://github.com/example/demo"
    )
    deployer.clone_repository.assert_called_once_with(
        "https://github.com/example/demo"
    )
    deployer.build_image.assert_called_once_with(
        repository_path="/tmp/example-demo",
        image_name="dockloom-example-demo:latest",
        docker_client=controller.client,
    )
    controller.deploy_replicas.assert_called_once_with(
        image="dockloom-example-demo:latest",
        replica_count=2,
        start_port=8080,
        container_port=8000,
        name_prefix="lcp-app-example-demo",
    )
    success.assert_called_once_with(
        "Deployed 2 replica(s) from example/demo."
    )
    mock_sync.assert_called_once_with(controller)


@patch.object(cli, "sync_load_balancer")
@patch.object(cli, "RepositoryDeployer")
def test_deploy_repository_clone_failure(mock_deployer_class, mock_sync):
    controller = MagicMock()
    deployer = mock_deployer_class.return_value

    deployer.validate_url.return_value = ("example", "demo")
    deployer.clone_repository.side_effect = RuntimeError("Clone failed")

    with (
        patch.object(
            cli.console,
            "input",
            side_effect=[
                "https://github.com/example/demo",
                "1",
                "8000",
                "8080",
            ],
        ),
        patch.object(cli, "print_error") as error,
    ):
        cli.deploy_repository(controller)

    error.assert_called_once_with("Repository deployment failed.")
    deployer.build_image.assert_not_called()
    controller.deploy_replicas.assert_not_called()
    mock_sync.assert_not_called()


@patch.object(cli, "sync_load_balancer")
@patch.object(cli, "RepositoryDeployer")
def test_deploy_repository_build_failure(mock_deployer_class, mock_sync):
    controller = MagicMock()
    deployer = mock_deployer_class.return_value

    deployer.validate_url.return_value = ("example", "demo")
    deployer.clone_repository.return_value = "/tmp/example-demo"
    deployer.build_image.side_effect = BuildError(
        "Build failed",
        build_log=[],
    )

    with (
        patch.object(
            cli.console,
            "input",
            side_effect=[
                "https://github.com/example/demo",
                "1",
                "8000",
                "8080",
            ],
        ),
        patch.object(cli, "print_error") as error,
    ):
        cli.deploy_repository(controller)

    error.assert_called_once_with("Repository deployment failed.")
    controller.deploy_replicas.assert_not_called()
    mock_sync.assert_not_called()
from unittest.mock import MagicMock

from controller.docker_controller import DockerController


def create_controller():
    mock_client = MagicMock()
    controller = DockerController(client=mock_client)
    return controller, mock_client


def test_list_containers():
    controller, mock_client = create_controller()

    container = MagicMock()
    container.short_id = "abc123"
    container.name = "lcp-app-1"
    container.status = "running"

    mock_client.containers.list.return_value = [container]

    result = controller.list_containers()

    assert result == [
        {
            "id": "abc123",
            "name": "lcp-app-1",
            "status": "running",
        }
    ]


def test_deploy():
    controller, mock_client = create_controller()

    container = MagicMock()
    container.short_id = "abc123"
    container.name = "lcp-app-3"
    container.status = "running"

    mock_client.containers.run.return_value = container

    result = controller.deploy(
        "lcp-app-3",
        "local-container-app:1.0",
        8003,
    )

    assert result == {
        "id": "abc123",
        "name": "lcp-app-3",
        "status": "running",
        "host_port": 8003,
    }

    mock_client.containers.run.assert_called_once_with(
        image="local-container-app:1.0",
        name="lcp-app-3",
        ports={"8000/tcp": 8003},
        environment={"CONTAINER_NAME": "lcp-app-3"},
        detach=True,
    )


def test_start():
    controller, mock_client = create_controller()

    container = MagicMock()
    container.name = "lcp-app-3"
    mock_client.containers.get.return_value = container

    result = controller.start("lcp-app-3")

    container.start.assert_called_once()

    assert result == {
        "name": "lcp-app-3",
        "status": "started",
    }


def test_stop():
    controller, mock_client = create_controller()

    container = MagicMock()
    container.name = "lcp-app-3"
    mock_client.containers.get.return_value = container

    result = controller.stop("lcp-app-3")

    container.stop.assert_called_once()

    assert result == {
        "name": "lcp-app-3",
        "status": "stopped",
    }


def test_remove():
    controller, mock_client = create_controller()

    container = MagicMock()
    mock_client.containers.get.return_value = container

    result = controller.remove("lcp-app-3")

    container.remove.assert_called_once()

    assert result == {
        "name": "lcp-app-3",
        "status": "removed",
    }

def test_deploy_replicas():
    mock_client = MagicMock()

    existing_container_1 = MagicMock()
    existing_container_1.short_id = "abc123"
    existing_container_1.name = "lcp-app-1"
    existing_container_1.status = "running"

    existing_container_2 = MagicMock()
    existing_container_2.short_id = "def456"
    existing_container_2.name = "lcp-app-2"
    existing_container_2.status = "running"

    existing_container_3 = MagicMock()
    existing_container_3.short_id = "ghi789"
    existing_container_3.name = "lcp-app-3"
    existing_container_3.status = "running"

    mock_container = MagicMock()
    mock_container.short_id = "new123"
    mock_container.name = "lcp-app-4"
    mock_container.status = "running"

    mock_client.containers.list.return_value = [
        existing_container_1,
        existing_container_2,
        existing_container_3,
    ]

    mock_client.containers.run.return_value = mock_container

    controller = DockerController(client=mock_client)

    replicas = controller.deploy_replicas(
        image="local-container-app:1.0",
        replica_count=3,
        start_port=8021,
    )

    assert len(replicas) == 3
    assert mock_client.containers.run.call_count == 3

    expected_calls = [
        {
            "image": "local-container-app:1.0",
            "name": "lcp-app-4",
            "ports": {"8000/tcp": 8021},
            "environment": {"CONTAINER_NAME": "lcp-app-4"},
            "detach": True,
        },
        {
            "image": "local-container-app:1.0",
            "name": "lcp-app-5",
            "ports": {"8000/tcp": 8022},
            "environment": {"CONTAINER_NAME": "lcp-app-5"},
            "detach": True,
        },
        {
            "image": "local-container-app:1.0",
            "name": "lcp-app-6",
            "ports": {"8000/tcp": 8023},
            "environment": {"CONTAINER_NAME": "lcp-app-6"},
            "detach": True,
        },
    ]

    actual_calls = [
        call.kwargs for call in mock_client.containers.run.call_args_list
    ]

    assert actual_calls == expected_calls
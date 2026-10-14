from controller.nginx_manager import NginxManager


def test_generate_upstream():
    manager = NginxManager("nginx/upstreams.conf")

    replicas = [
        {"name": "lcp-app-1", "host_port": 8011},
        {"name": "lcp-app-2", "host_port": 8012},
        {"name": "lcp-app-3", "host_port": 8013},
    ]

    config = manager.generate_upstream(replicas)

    expected = (
        "upstream local_container_backend {\n"
        "    zone local_container_backend 64k;\n"
        "    server 127.0.0.1:8011;\n"
        "    server 127.0.0.1:8012;\n"
        "    server 127.0.0.1:8013;\n"
        "}"
    )

    assert config == expected


def test_write_config(tmp_path):
    config_path = tmp_path / "upstreams.conf"

    manager = NginxManager(config_path)

    replicas = [
        {"name": "lcp-app-1", "host_port": 8011},
        {"name": "lcp-app-2", "host_port": 8012},
    ]

    manager.write_config(replicas)

    assert config_path.read_text() == (
    "upstream local_container_backend {\n"
    "    zone local_container_backend 64k;\n"
    "    server 127.0.0.1:8011;\n"
    "    server 127.0.0.1:8012;\n"
    "}\n"
)

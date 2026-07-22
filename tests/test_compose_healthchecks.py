from pathlib import Path


def test_scheduler_healthcheck_allows_for_python_startup() -> None:
    compose = (Path(__file__).parents[1] / "docker-compose.yml").read_text()

    scheduler = compose.split("  scheduler:\n", maxsplit=1)[1].split("\n  nginx:\n", maxsplit=1)[0]

    assert 'test: ["CMD", "python", "-m", "app.workers.scheduler", "--healthcheck"]' in scheduler
    assert "timeout: 15s" in scheduler


def test_cloudflared_override_exposes_only_api_on_loopback() -> None:
    override = (Path(__file__).parents[1] / "deploy" / "docker-compose.cloudflared.yml").read_text()

    assert '"127.0.0.1:${API_HOST_PORT:-8081}:${APP_PORT:-8080}"' in override
    assert "postgres:" not in override
    assert "redis:" not in override
    assert "profiles:" in override


def test_deploy_helper_applies_cloudflared_override_from_environment() -> None:
    helper = (Path(__file__).parents[1] / "deploy" / "lib" / "common.sh").read_text()

    assert 'ingress="$(env_value DEPLOY_INGRESS)"' in helper
    assert "deploy/docker-compose.cloudflared.yml" in helper


def test_runtime_directories_are_initialized_for_unprivileged_services() -> None:
    compose = (Path(__file__).parents[1] / "docker-compose.yml").read_text()

    runtime_init = compose.split("  runtime-init:\n", maxsplit=1)[1].split(
        "\n  api:\n", maxsplit=1
    )[0]
    assert "user: root" in runtime_init
    assert "- CHOWN" in runtime_init
    assert "- DAC_OVERRIDE" in runtime_init
    assert "- FOWNER" in runtime_init
    assert "chown -R appuser:appuser /app/data /app/backups" in runtime_init
    assert compose.count("runtime-init:\n        condition: service_completed_successfully") == 3

from pathlib import Path


def test_scheduler_healthcheck_allows_for_python_startup() -> None:
    compose = (Path(__file__).parents[1] / "docker-compose.yml").read_text()

    scheduler = compose.split("  scheduler:\n", maxsplit=1)[1].split("\n  nginx:\n", maxsplit=1)[0]

    assert 'test: ["CMD", "python", "-m", "app.workers.scheduler", "--healthcheck"]' in scheduler
    assert "timeout: 15s" in scheduler

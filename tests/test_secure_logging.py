import json
import logging
from pathlib import Path

from app.core.logging import JsonFormatter


def test_json_formatter_redacts_callback_signatures_and_credentials() -> None:
    record = logging.LogRecord(
        name="security-test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=(
            "GET /success?SignatureValue=callback-signature&access_token=oauth-token "
            'payload={"client_secret":"client-credential"}'  # pragma: allowlist secret
        ),
        args=(),
        exc_info=None,
    )

    payload = json.loads(JsonFormatter().format(record))

    assert "callback-signature" not in payload["message"]
    assert "oauth-token" not in payload["message"]
    assert "client-credential" not in payload["message"]
    assert payload["message"].count("[REDACTED]") == 3


def test_http_access_logs_cannot_include_query_parameters() -> None:
    root = Path(__file__).parents[1]
    compose = (root / "docker-compose.yml").read_text()
    assert "--no-access-log" in compose

    for template_name in ("http.conf.template", "https.conf.template"):
        template = (root / "deploy" / "nginx" / "templates" / template_name).read_text()
        log_format = template.split("server {", maxsplit=1)[0]
        assert "$uri" in log_format
        assert "$request_uri" not in log_format
        assert "$args" not in log_format
        assert "$http_referer" not in log_format

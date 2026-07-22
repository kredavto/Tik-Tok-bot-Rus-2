"""Validate the public API contract without starting infrastructure services."""

from app.api.main import app

REQUIRED_OPERATIONS = {
    ("/api/v1/health", "get"),
    ("/api/v1/ready", "get"),
    ("/api/v1/metrics", "get"),
    ("/api/v1/oauth/tiktok/start", "get"),
    ("/api/v1/oauth/tiktok/callback", "get"),
    ("/api/v1/webhooks/telegram", "post"),
    ("/api/v1/webhooks/tiktok", "post"),
    ("/api/v1/payments/robokassa/result", "post"),
    ("/api/v1/payments/robokassa/success", "get"),
    ("/api/v1/payments/robokassa/fail", "get"),
}


def validate_openapi() -> None:
    schema = app.openapi()
    if not str(schema.get("openapi", "")).startswith("3."):
        raise RuntimeError("OpenAPI 3.x schema is required")

    missing = [
        f"{method.upper()} {path}"
        for path, method in sorted(REQUIRED_OPERATIONS)
        if method not in schema.get("paths", {}).get(path, {})
    ]
    if missing:
        raise RuntimeError(f"Missing required API operations: {', '.join(missing)}")

    operation_ids: list[str] = []
    for path_item in schema.get("paths", {}).values():
        for method, operation in path_item.items():
            if method.lower() in {"get", "post", "put", "patch", "delete"}:
                operation_id = operation.get("operationId")
                if operation_id:
                    operation_ids.append(operation_id)
    duplicates = sorted({item for item in operation_ids if operation_ids.count(item) > 1})
    if duplicates:
        raise RuntimeError(f"Duplicate OpenAPI operation IDs: {', '.join(duplicates)}")


if __name__ == "__main__":
    validate_openapi()
    print("OpenAPI contract is valid")

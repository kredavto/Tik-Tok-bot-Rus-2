from app.bot import messages


def test_message_template_can_be_loaded_before_formatting() -> None:
    assert "{used}" in messages.LIMIT_EXCEEDED
    assert messages.LIMIT_EXCEEDED.format(used=2, limit=2).startswith("Лимит")


def test_message_catalog_formats_when_values_are_provided() -> None:
    assert messages.text("payment_success", plan="PRO") == (
        "Оплата получена. Подписка PRO активирована на 30 дней."
    )

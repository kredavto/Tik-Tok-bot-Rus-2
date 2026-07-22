import hashlib
import hmac
from decimal import Decimal
from urllib.parse import urlencode

from app.core.config import settings


def _signature(*parts: object, algorithm: str | None = None) -> str:
    source = ":".join(str(part) for part in parts)
    return hashlib.new(
        algorithm or settings.robokassa_hash_algorithm,
        source.encode("utf-8"),
    ).hexdigest()


def build_payment_url(inv_id: int, amount_rub: int, description: str) -> str:
    out_sum = f"{Decimal(amount_rub):.2f}"
    signature = _signature(
        settings.robokassa_login,
        out_sum,
        inv_id,
        settings.robokassa_password1,
    )
    params = {
        "MerchantLogin": settings.robokassa_login,
        "OutSum": out_sum,
        "InvId": inv_id,
        "Description": description,
        "SignatureValue": signature,
        "Culture": "ru",
        "Encoding": "utf-8",
    }
    if settings.robokassa_test_mode:
        params["IsTest"] = 1
    return f"https://auth.robokassa.ru/Merchant/Index.aspx?{urlencode(params)}"


def validate_result_signature(out_sum: str, inv_id: str, signature_value: str) -> bool:
    expected = _signature(out_sum, inv_id, settings.robokassa_password2)
    return hmac.compare_digest(expected.lower(), signature_value.lower())

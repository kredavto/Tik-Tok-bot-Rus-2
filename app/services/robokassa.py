from hashlib import md5
from urllib.parse import urlencode

from app.core.config import settings


def _signature(*parts: object) -> str:
    source = ":".join(str(part) for part in parts)
    return md5(source.encode("utf-8")).hexdigest()


def build_payment_url(inv_id: int, amount_rub: int, description: str) -> str:
    signature = _signature(
        settings.robokassa_login,
        amount_rub,
        inv_id,
        settings.robokassa_password1,
    )
    params = {
        "MerchantLogin": settings.robokassa_login,
        "OutSum": amount_rub,
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
    return expected.lower() == signature_value.lower()

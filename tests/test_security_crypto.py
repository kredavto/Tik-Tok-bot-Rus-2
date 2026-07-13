from cryptography.fernet import Fernet

from app.security.crypto import decrypt_secret, encrypt_secret


def test_encrypts_and_decrypts_token(monkeypatch) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "token_encryption_key", Fernet.generate_key().decode("utf-8"))

    encrypted = encrypt_secret("access-token")

    assert encrypted != "access-token"
    assert decrypt_secret(encrypted) == "access-token"

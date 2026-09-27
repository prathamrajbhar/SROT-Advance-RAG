import base64
import os
import pytest
from core.crypto import (
    CryptoError,
    InvalidKeyError,
    InvalidPayloadError,
    SecretVault,
    TamperError,
    get_secret_vault,
)


@pytest.fixture
def master_key_bytes() -> bytes:
    return os.urandom(32)


@pytest.fixture
def vault(master_key_bytes: bytes) -> SecretVault:
    return SecretVault(master_key_bytes)


def test_vault_initialization_with_valid_keys(master_key_bytes: bytes):
    vault_from_bytes = SecretVault(master_key_bytes)
    assert vault_from_bytes is not None

    hex_key = master_key_bytes.hex()
    vault_from_hex = SecretVault(hex_key)
    assert vault_from_hex is not None

    b64_key = base64.b64encode(master_key_bytes).decode("utf-8")
    vault_from_b64 = SecretVault(b64_key)
    assert vault_from_b64 is not None

    raw_32_str = "a" * 32
    vault_from_str = SecretVault(raw_32_str)
    assert vault_from_str is not None


def test_vault_initialization_with_invalid_key_length():
    with pytest.raises(InvalidKeyError):
        SecretVault(b"too_short_key")

    with pytest.raises(InvalidKeyError):
        SecretVault("short_hex")

    with pytest.raises(InvalidKeyError):
        SecretVault(b"a" * 33)


def test_encrypt_decrypt_roundtrip(vault: SecretVault):
    test_cases = [
        "mock_sample_api_token_abc123",
        "mock_gemini_token_xyz789",

        "",  # empty secret
        "Special chars: !@#$%^&*()_+{}[]:;\"'<>?,./~`",
        "Unicode: 秘密鍵 🔑 🔒 ✨",
        "A" * 4096,  # long secret
    ]

    for plaintext in test_cases:
        encrypted = vault.encrypt_secret(plaintext)
        assert isinstance(encrypted, str)
        assert encrypted != plaintext

        decrypted = vault.decrypt_secret(encrypted)
        assert decrypted == plaintext


def test_nonce_uniqueness(vault: SecretVault):
    plaintext = "super_sensitive_api_key_1234"
    ciphertext1 = vault.encrypt_secret(plaintext)
    ciphertext2 = vault.encrypt_secret(plaintext)

    assert ciphertext1 != ciphertext2
    assert vault.decrypt_secret(ciphertext1) == plaintext
    assert vault.decrypt_secret(ciphertext2) == plaintext


def test_tamper_detection(vault: SecretVault):
    plaintext = "sk-test-super-secret-production-token"
    encrypted = vault.encrypt_secret(plaintext)

    raw_bytes = bytearray(base64.b64decode(encrypted))
    # Flip the last bit of the auth tag
    raw_bytes[-1] ^= 0x01
    tampered_payload = base64.b64encode(raw_bytes).decode("utf-8")

    with pytest.raises(TamperError):
        vault.decrypt_secret(tampered_payload)


def test_nonce_tampering(vault: SecretVault):
    plaintext = "sk-test-super-secret-production-token"
    encrypted = vault.encrypt_secret(plaintext)

    raw_bytes = bytearray(base64.b64decode(encrypted))
    # Flip a bit in the nonce (first 12 bytes)
    raw_bytes[0] ^= 0x01
    tampered_payload = base64.b64encode(raw_bytes).decode("utf-8")

    with pytest.raises(TamperError):
        vault.decrypt_secret(tampered_payload)


def test_invalid_payload_handling(vault: SecretVault):
    with pytest.raises(InvalidPayloadError):
        vault.decrypt_secret("not-a-valid-base64-string!@#$")

    # Valid base64 but shorter than 28 bytes (12 nonce + 16 auth tag)
    short_payload = base64.b64encode(b"short").decode("utf-8")
    with pytest.raises(InvalidPayloadError):
        vault.decrypt_secret(short_payload)


def test_mask_secret(vault: SecretVault):
    assert vault.mask_secret("") == "••••••••"
    assert vault.mask_secret("1234567") == "••••••••"
    assert vault.mask_secret("12345678") == "••••••••"
    assert vault.mask_secret("123456789") == "••••••••6789"
    assert vault.mask_secret("sk-proj-abcde12345XYZ") == "••••••••5XYZ"


def test_get_secret_vault_factory():
    vault_instance = get_secret_vault()
    assert isinstance(vault_instance, SecretVault)
    encrypted = vault_instance.encrypt_secret("factory_test_secret")
    assert vault_instance.decrypt_secret(encrypted) == "factory_test_secret"

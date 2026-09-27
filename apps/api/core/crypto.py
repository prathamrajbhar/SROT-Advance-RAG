import base64
import os
from typing import Union
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from core.config import get_settings


class CryptoError(Exception):
    """Base exception for cryptographic operations."""


class InvalidKeyError(CryptoError):
    """Raised when the master encryption key is invalid."""


class InvalidPayloadError(CryptoError):
    """Raised when an encrypted payload is malformed or unparseable."""


class TamperError(CryptoError):
    """Raised when ciphertext authentication fails due to tampering."""


class SecretVault:
    """AES-256-GCM envelope encryption vault for sensitive tenant secrets."""

    NONCE_BYTE_LENGTH: int = 12
    AUTH_TAG_BYTE_LENGTH: int = 16
    MIN_PAYLOAD_BYTE_LENGTH: int = NONCE_BYTE_LENGTH + AUTH_TAG_BYTE_LENGTH

    def __init__(self, master_key: Union[bytes, str]) -> None:
        key_bytes = self._normalize_key(master_key)
        if len(key_bytes) != 32:
            raise InvalidKeyError(
                f"Master encryption key must be exactly 32 bytes (256 bits). Received {len(key_bytes)} bytes."
            )
        self._aesgcm = AESGCM(key_bytes)

    @staticmethod
    def _normalize_key(master_key: Union[bytes, str]) -> bytes:
        if isinstance(master_key, bytes):
            return master_key

        trimmed_key = master_key.strip()
        if len(trimmed_key) == 64:
            try:
                return bytes.fromhex(trimmed_key)
            except ValueError:
                pass

        try:
            decoded_base64 = base64.b64decode(trimmed_key)
            if len(decoded_base64) == 32:
                return decoded_base64
        except Exception:
            pass

        return trimmed_key.encode("utf-8")

    def encrypt_secret(self, plaintext: str) -> str:
        """Encrypts plaintext using AES-256-GCM with a fresh 96-bit nonce."""
        nonce_bytes = os.urandom(self.NONCE_BYTE_LENGTH)
        raw_ciphertext = self._aesgcm.encrypt(
            nonce_bytes,
            plaintext.encode("utf-8"),
            None,
        )
        combined_payload = nonce_bytes + raw_ciphertext
        return base64.b64encode(combined_payload).decode("utf-8")

    def decrypt_secret(self, encrypted_payload: str) -> str:
        """Decrypts base64-encoded AES-256-GCM payload with tamper verification."""
        try:
            combined_bytes = base64.b64decode(encrypted_payload.encode("utf-8"), validate=True)
        except Exception as decode_error:
            raise InvalidPayloadError(f"Invalid base64 payload: {decode_error}") from decode_error

        if len(combined_bytes) < self.MIN_PAYLOAD_BYTE_LENGTH:
            raise InvalidPayloadError(
                f"Payload length {len(combined_bytes)} bytes is shorter than minimum required "
                f"({self.MIN_PAYLOAD_BYTE_LENGTH} bytes)."
            )

        nonce_bytes = combined_bytes[: self.NONCE_BYTE_LENGTH]
        ciphertext_and_tag = combined_bytes[self.NONCE_BYTE_LENGTH :]

        try:
            decrypted_bytes = self._aesgcm.decrypt(nonce_bytes, ciphertext_and_tag, None)
            return decrypted_bytes.decode("utf-8")
        except InvalidTag as auth_error:
            raise TamperError(
                "Payload authentication failed: ciphertext or tag has been tampered with."
            ) from auth_error

    @staticmethod
    def mask_secret(plaintext: str) -> str:
        """Masks sensitive secret, revealing only the last 4 characters if long enough."""
        if len(plaintext) <= 8:
            return "••••••••"
        return f"••••••••{plaintext[-4:]}"


def get_secret_vault() -> SecretVault:
    """Factory dependency returning configured SecretVault instance."""
    app_settings = get_settings()
    return SecretVault(app_settings.ENCRYPTION_MASTER_KEY)

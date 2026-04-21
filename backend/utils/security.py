import base64
import hashlib
import os
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def _sha256_bytes(value: str) -> bytes:
	return hashlib.sha256((value or "").encode("utf-8")).digest()


def _security_master_key() -> bytes:
	configured = (os.getenv("DATA_SECURITY_KEY") or "").strip()
	if configured:
		try:
			decoded = base64.urlsafe_b64decode(configured + "=" * (-len(configured) % 4))
			if len(decoded) == 32:
				return decoded
		except Exception:
			pass
		if len(configured) >= 32:
			return _sha256_bytes(configured)

	fallback = (os.getenv("SESSION_SECRET") or os.getenv("MONGO_URI") or "echothread-security-fallback").strip()
	return _sha256_bytes(fallback)


def email_hash(email: Optional[str]) -> str:
	value = (email or "").strip().lower()
	return hashlib.sha256(value.encode("utf-8")).hexdigest()


def encrypt_text(plain_text: Optional[str], *, aad: str = "") -> str:
	value = (plain_text or "")
	key = _security_master_key()
	aesgcm = AESGCM(key)
	nonce = os.urandom(12)
	cipher = aesgcm.encrypt(nonce, value.encode("utf-8"), aad.encode("utf-8") if aad else None)
	return base64.urlsafe_b64encode(nonce + cipher).decode("utf-8")


def decrypt_text(cipher_text: Optional[str], *, aad: str = "") -> str:
	value = (cipher_text or "").strip()
	if not value:
		return ""
	try:
		raw = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
		if len(raw) <= 12:
			return ""
		nonce, cipher = raw[:12], raw[12:]
		aesgcm = AESGCM(_security_master_key())
		plain = aesgcm.decrypt(nonce, cipher, aad.encode("utf-8") if aad else None)
		return plain.decode("utf-8")
	except Exception:
		return ""

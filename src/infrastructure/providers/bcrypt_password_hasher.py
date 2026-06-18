"""bcrypt implementation of IPasswordHasher."""
import base64
import hashlib

import bcrypt

from ...core.interfaces.providers.i_password_hasher import IPasswordHasher


class BcryptPasswordHasher(IPasswordHasher):
    """
    Password hasher backed by bcrypt.

    bcrypt only considers the first 72 bytes of input, so we first SHA-256 the
    password and base64-encode the digest before hashing. This removes the
    length limit (and avoids bcrypt raising on >72-byte inputs) without weakening
    the hash.
    """

    def __init__(self, rounds: int = 12):
        self._rounds = rounds

    def _prehash(self, plaintext: str) -> bytes:
        digest = hashlib.sha256(plaintext.encode("utf-8")).digest()
        return base64.b64encode(digest)

    def hash(self, plaintext: str) -> str:
        salt = bcrypt.gensalt(rounds=self._rounds)
        return bcrypt.hashpw(self._prehash(plaintext), salt).decode("utf-8")

    def verify(self, plaintext: str, password_hash: str) -> bool:
        try:
            return bcrypt.checkpw(self._prehash(plaintext), password_hash.encode("utf-8"))
        except (ValueError, TypeError):
            # Malformed stored hash — treat as a non-match rather than erroring.
            return False

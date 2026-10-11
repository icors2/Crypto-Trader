from __future__ import annotations

import hmac
import secrets
import time
from collections import defaultdict

import bcrypt
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from crypto_trader.settings import EnvSettings

SESSION_MAX_AGE = 12 * 60 * 60
LOGIN_WINDOW_SEC = 15 * 60
LOGIN_MAX_ATTEMPTS = 5


class Auth:
    def __init__(self, settings: EnvSettings) -> None:
        self.settings = settings
        self.serializer = URLSafeTimedSerializer(settings.ui_session_secret, salt="ui-session")
        self._attempts: dict[str, list[float]] = defaultdict(list)
        password = settings.ui_password
        if settings.ui_password_hash:
            self._hash = settings.ui_password_hash.encode("utf-8")
        elif password:
            self._hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        else:
            generated = secrets.token_urlsafe(12)
            self._hash = bcrypt.hashpw(generated.encode("utf-8"), bcrypt.gensalt())
            self.generated_password = generated
        if not hasattr(self, "generated_password"):
            self.generated_password = None

    def rate_limited(self, ip: str) -> bool:
        now = time.time()
        hits = [t for t in self._attempts[ip] if now - t < LOGIN_WINDOW_SEC]
        self._attempts[ip] = hits
        return len(hits) >= LOGIN_MAX_ATTEMPTS

    def record_attempt(self, ip: str) -> None:
        self._attempts[ip].append(time.time())

    def verify_password(self, password: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode("utf-8"), self._hash)
        except ValueError:
            return hmac.compare_digest(password, "")

    def issue_session(self) -> str:
        csrf = secrets.token_urlsafe(16)
        return self.serializer.dumps({"csrf": csrf})

    def load_session(self, token: str | None) -> dict | None:
        if not token:
            return None
        try:
            return self.serializer.loads(token, max_age=SESSION_MAX_AGE)
        except (BadSignature, SignatureExpired):
            return None

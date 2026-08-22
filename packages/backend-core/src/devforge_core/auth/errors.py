class AuthError(ValueError):
    code = "auth_error"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.code)


class InvalidCredentials(AuthError):
    code = "invalid_credentials"


class EmailAlreadyExists(AuthError):
    code = "email_already_exists"


class PasswordPolicyViolation(AuthError):
    code = "password_policy_violation"

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


class AuthorizationDenied(AuthError):
    code = "authorization_denied"

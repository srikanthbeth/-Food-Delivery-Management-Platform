class AuthenticationException(Exception):

    def __init__(
        self,
        message: str = "Authentication failed",
    ):
        self.message = message
        super().__init__(message)


class AuthorizationException(Exception):

    def __init__(
        self,
        message: str = "Access denied",
    ):
        self.message = message
        super().__init__(message)


class ResourceNotFoundException(Exception):

    def __init__(
        self,
        message: str = "Resource not found",
    ):
        self.message = message
        super().__init__(message)


class BusinessRuleException(Exception):

    def __init__(
        self,
        message: str,
    ):
        self.message = message
        super().__init__(message)
class PermissionDeniedException(Exception):
    pass
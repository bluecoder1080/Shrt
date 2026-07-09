class AppError(Exception):
    def __init__(self, message: str, status_code: int):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class AuthenticationError(AppError):
    def __init__(self, message: str = "Could not validate credentials"):
        super().__init__(message, 401)

class ForbiddenError(AppError):
    def __init__(self, message: str = "Not authorized to access this resource"):
        super().__init__(message, 403)

class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, 404)

class ConflictError(AppError):
    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message, 409)

class ExpiredError(AppError):
    def __init__(self, message: str = "URL has expired"):
        super().__init__(message, 410)

class ValidationError(AppError):
    def __init__(self, message: str = "Validation error"):
        super().__init__(message, 422)

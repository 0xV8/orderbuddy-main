"""Custom exceptions"""

from fastapi import HTTPException, status


class AppException(HTTPException):
    """Base application exception"""

    def __init__(self, status_code: int, message: str, detail: str = None):
        super().__init__(status_code=status_code, detail=message)
        self.message = message
        self.detail = detail


class NotFoundException(AppException):
    """Resource not found exception"""

    def __init__(self, resource: str, identifier: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=f"{resource} not found",
            detail=f"{resource} with ID '{identifier}' does not exist",
        )


class BadRequestException(AppException):
    """Bad request exception"""

    def __init__(self, message: str, detail: str = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST, message=message, detail=detail
        )


class UnauthorizedException(AppException):
    """Unauthorized exception"""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, message=message)

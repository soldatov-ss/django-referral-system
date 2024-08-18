from typing import Union


class BaseAPIException(Exception):
    """
    Base API exception.
    """

    def __init__(self, error_message: Union[str, dict], status_code: int):
        self.error_message = error_message
        self.status_code = status_code
        super().__init__(self.error_message)


class ViewException(BaseAPIException):
    """Base view exception."""

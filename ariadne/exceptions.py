from .constants import HTTP_STATUS_400_BAD_REQUEST, HTTP_STATUS_405_METHOD_NOT_ALLOWED


class HttpError(Exception):
    status = ""

    def __init__(self, message=None):
        super().__init__()
        self.message = message


class HttpBadRequestError(HttpError):
    status = HTTP_STATUS_400_BAD_REQUEST


class HttpMethodNotAllowedError(HttpError):
    status = HTTP_STATUS_405_METHOD_NOT_ALLOWED


class GraphQLError(Exception):
    pass

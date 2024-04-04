from enum import Enum
from http import HTTPStatus

DATA_TYPE_JSON = "application/json"
DATA_TYPE_MULTIPART = "multipart/form-data"

CONTENT_TYPE_JSON = "application/json; charset=UTF-8"
CONTENT_TYPE_TEXT_HTML = "text/html; charset=UTF-8"
CONTENT_TYPE_TEXT_PLAIN = "text/plain; charset=UTF-8"


class HttpStatusResponse(Enum):
    OK = f"{HTTPStatus.OK} OK"
    BAD_REQUEST = f"{HTTPStatus.BAD_REQUEST} BAD REQUEST"
    METHOD_NOT_ALLOWED = f"{HTTPStatus.METHOD_NOT_ALLOWED} METHOD NOT ALLOWED"

import json
from typing import Optional

from starlette.datastructures import UploadFile
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response
from starlette.types import Receive, Scope, Send

from graphql import GraphQLSchema

from ...file_uploads import combine_multipart_data
from ...format_error import format_error
from ...types import (
    ContextValue,
    ErrorFormatter,
    RootValue,
    ValidationRules,
    Extensions,
    Middlewares,
)
from ...exceptions import HttpBadRequestError, HttpError
from ...constants import (
    DATA_TYPE_JSON,
    DATA_TYPE_MULTIPART,
    PLAYGROUND_HTML,
)

from .graphql_base import GraphQLBase


class GraphQLHTTP(GraphQLBase):
    def __init__(
        self,
        schema: GraphQLSchema,
        context_value: Optional[ContextValue] = None,
        root_value: Optional[RootValue] = None,
        validation_rules: Optional[ValidationRules] = None,
        debug: bool = False,
        introspection: bool = True,
        logger: Optional[str] = None,
        error_formatter: ErrorFormatter = format_error,
        extensions: Optional[Extensions] = None,
        middleware: Optional[Middlewares] = None,
    ):
        super().__init__()
        self.context_value = context_value
        self.root_value = root_value
        self.validation_rules = validation_rules
        self.debug = debug
        self.introspection = introspection
        self.logger = logger
        self.error_formatter = error_formatter
        self.extensions = extensions
        self.middleware = middleware
        self.schema = schema

    async def handle_http(self, scope: Scope, receive: Receive, send: Send):
        request = Request(scope=scope, receive=receive)
        if request.method == "GET" and self.introspection:
            # only render playground when introspection is enabled
            response = await self.render_playground(request)
        elif request.method == "POST":
            response = await self.graphql_http_server(request)
        else:
            response = self.handle_not_allowed_method(request)
        await response(scope, receive, send)

    async def render_playground(  # pylint: disable=unused-argument
        self, request: Request
    ) -> Response:
        return HTMLResponse(PLAYGROUND_HTML)

    async def graphql_http_server(self, request: Request) -> Response:
        try:
            data = await self.extract_data_from_request(request)
        except HttpError as error:
            return PlainTextResponse(error.message or error.status, status_code=400)

        success, result = await self.execute_graphql_query(request, data)
        return await self.create_json_response(request, result, success)

    async def create_json_response(
        self,
        request: Request,  # pylint: disable=unused-argument
        result: dict,
        success: bool,
    ) -> Response:
        status_code = 200 if success else 400
        return JSONResponse(result, status_code=status_code)

    async def extract_data_from_request(self, request: Request):
        content_type = request.headers.get("Content-Type", "")
        content_type = content_type.split(";")[0]

        if content_type == DATA_TYPE_JSON:
            return await self.extract_data_from_json_request(request)
        if content_type == DATA_TYPE_MULTIPART:
            return await self.extract_data_from_multipart_request(request)

        raise HttpBadRequestError(
            "Posted content must be of type {} or {}".format(
                DATA_TYPE_JSON, DATA_TYPE_MULTIPART
            )
        )

    async def extract_data_from_json_request(self, request: Request):
        try:
            return await request.json()
        except (TypeError, ValueError) as ex:
            raise HttpBadRequestError("Request body is not a valid JSON") from ex

    async def extract_data_from_multipart_request(self, request: Request):
        try:
            request_body = await request.form()
        except ValueError as ex:
            raise HttpBadRequestError(
                "Request body is not a valid multipart/form-data"
            ) from ex

        try:
            operations = json.loads(request_body.get("operations"))
        except (TypeError, ValueError) as ex:
            raise HttpBadRequestError(
                "Request 'operations' multipart field is not a valid JSON"
            ) from ex
        try:
            files_map = json.loads(request_body.get("map"))
        except (TypeError, ValueError) as ex:
            raise HttpBadRequestError(
                "Request 'map' multipart field is not a valid JSON"
            ) from ex

        request_files = {
            key: value
            for key, value in request_body.items()
            if isinstance(value, UploadFile)
        }

        return combine_multipart_data(operations, files_map, request_files)

    def handle_not_allowed_method(self, request: Request):
        allowed_methods = ["OPTIONS", "POST"]
        if self.introspection:
            allowed_methods.append("GET")
        allow_header = {"Allow": ", ".join(allowed_methods)}

        if request.method == "OPTIONS":
            return Response(headers=allow_header)

        return Response(status_code=405, headers=allow_header)

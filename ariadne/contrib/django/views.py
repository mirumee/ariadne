import json
from typing import Optional, cast

from django.conf import settings
from django.http import HttpRequest, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from graphql import GraphQLSchema
from graphql.execution import MiddlewareManager

from ...constants import DATA_TYPE_JSON, DATA_TYPE_MULTIPART
from ...exceptions import HttpBadRequestError
from ...file_uploads import combine_multipart_data
from ...format_error import format_error
from ...graphql import graphql_sync
from ...types import ContextValue, ErrorFormatter, GraphQLResult, RootValue


DEFAULT_PLAYGROUND_OPTIONS = {"request.credentials": "same-origin"}


@method_decorator(csrf_exempt, name="dispatch")
class GraphQLView(TemplateView):
    http_method_names = ["get", "post", "options"]
    template_name = "ariadne/graphql_playground.html"
    playground_options: Optional[dict] = None
    schema: Optional[GraphQLSchema] = None
    context_value: Optional[ContextValue] = None
    root_value: Optional[RootValue] = None
    logger = None
    validation_rules = None
    error_formatter: Optional[ErrorFormatter] = None
    middleware: Optional[MiddlewareManager] = None

    def get(
        self, request: HttpRequest, *args, **kwargs
    ):  # pylint: disable=unused-argument
        options = DEFAULT_PLAYGROUND_OPTIONS.copy()
        if self.playground_options:
            options.update(self.playground_options)

        return render(
            request,
            self.get_template_names(),
            {"playground_options": json.dumps(options)},
        )

    def post(
        self, request: HttpRequest, *args, **kwargs
    ):  # pylint: disable=unused-argument
        if not self.schema:
            raise ValueError("GraphQLView was initialized without schema.")

        try:
            data = self.extract_data_from_request(request)
        except HttpBadRequestError as error:
            return HttpResponseBadRequest(error.message)

        success, result = self.execute_query(request, data)
        status_code = 200 if success else 400
        return JsonResponse(result, status=status_code)

    def extract_data_from_request(self, request: HttpRequest):
        content_type = request.content_type or ""
        content_type = content_type.split(";")[0]

        if content_type == DATA_TYPE_JSON:
            return self.extract_data_from_json_request(request)
        if content_type == DATA_TYPE_MULTIPART:
            return self.extract_data_from_multipart_request(request)

        raise HttpBadRequestError(
            "Posted content must be of type {} or {}".format(
                DATA_TYPE_JSON, DATA_TYPE_MULTIPART
            )
        )

    def extract_data_from_json_request(self, request: HttpRequest):
        try:
            return json.loads(request.body)
        except (TypeError, ValueError):
            raise HttpBadRequestError("Request body is not a valid JSON")

    def extract_data_from_multipart_request(self, request: HttpRequest):
        try:
            operations = json.loads(request.POST.get("operations"))
        except (TypeError, ValueError):
            raise HttpBadRequestError(
                "Request 'operations' multipart field is not a valid JSON"
            )
        try:
            files_map = json.loads(request.POST.get("map"))
        except (TypeError, ValueError):
            raise HttpBadRequestError(
                "Request 'map' multipart field is not a valid JSON"
            )

        return combine_multipart_data(operations, files_map, request.FILES)

    def execute_query(self, request: HttpRequest, data: dict) -> GraphQLResult:
        if callable(self.context_value):
            context_value = self.context_value(request)  # pylint: disable=not-callable
        else:
            context_value = self.context_value or request

        return graphql_sync(
            cast(GraphQLSchema, self.schema),
            data,
            context_value=context_value,
            root_value=self.root_value,
            debug=settings.DEBUG,
            logger=self.logger,
            validation_rules=self.validation_rules,
            error_formatter=self.error_formatter or format_error,
            middleware=self.middleware,
        )

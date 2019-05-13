import json
from typing import Optional, cast

from django.conf import settings
from django.http import HttpRequest, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from graphql import GraphQLSchema

from ...constants import DATA_TYPE_JSON
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
    middleware = None

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

        if request.content_type != DATA_TYPE_JSON:
            return HttpResponseBadRequest(
                "Posted content must be of type {}".format(DATA_TYPE_JSON)
            )

        try:
            data = json.loads(request.body)
        except ValueError:
            return HttpResponseBadRequest("Request body is not a valid JSON")

        success, result = self.execute_query(request, data)
        status_code = 200 if success else 400
        return JsonResponse(result, status=status_code)

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

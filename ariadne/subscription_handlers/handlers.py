"""Subscription handler base class for HTTP-based subscription protocols."""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from logging import Logger, LoggerAdapter
from typing import Any, cast

from graphql import DocumentNode, ExecutionResult, GraphQLError, GraphQLSchema
from starlette.requests import Request
from starlette.responses import Response

from ..graphql import subscribe, validate_data
from ..logger import log_error
from ..types import (
    ErrorFormatter,
    QueryParser,
    QueryValidator,
    RootValue,
    ValidationRules,
)
from .events import SubscriptionEvent, SubscriptionEventType


class SubscriptionHandler(ABC):
    """Base class for HTTP-based subscription handlers.

    Provides the `generate_events` method that handles the subscription
    execution and yields `SubscriptionEvent` objects. Subclasses are used
    with `GraphQLHTTPHandler` via its `subscription_handlers` parameter.
    WebSocket-based subscriptions are handled separately by dedicated
    handlers (`GraphQLWSHandler` and `GraphQLTransportWSHandler`).
    """

    @abstractmethod
    def supports(self, request: Request, data: dict) -> bool:
        """Determine if this handler supports the given request.

        # Required arguments
        `request`: the Starlette/FastAPI request
        `data`: the parsed GraphQL request data

        # Returns
        `True` if this handler can handle the request, `False` otherwise.
        """

    @abstractmethod
    async def handle(
        self,
        request: Request,
        data: dict,
        *,
        schema: GraphQLSchema,
        context_value: Any,
        root_value: RootValue | None,
        query_parser: QueryParser | None,
        query_validator: QueryValidator | None,
        validation_rules: ValidationRules | None,
        debug: bool,
        introspection: bool,
        logger: None | str | Logger | LoggerAdapter,
        error_formatter: ErrorFormatter,
    ) -> Response:
        """Handle the subscription request."""

    async def generate_events(
        self,
        data: dict,
        *,
        schema: GraphQLSchema,
        context_value: Any,
        root_value: RootValue | None,
        query_parser: QueryParser | None,
        query_validator: QueryValidator | None,
        query_document: DocumentNode | None,
        validation_rules: ValidationRules | None,
        debug: bool,
        introspection: bool,
        logger: None | str | Logger | LoggerAdapter,
        error_formatter: ErrorFormatter,
    ) -> AsyncGenerator[SubscriptionEvent, None]:
        """Execute subscription and yield events.

        This method handles the subscription execution lifecycle:
        1. Validates the request data
        2. Calls the GraphQL subscribe function
        3. Yields SubscriptionEvent objects for each result
        4. Handles errors appropriately

        # Yields
        `SubscriptionEvent` objects for each subscription result or error.
        """
        try:
            validate_data(data)

            success, results = await subscribe(
                schema,
                data,
                context_value=context_value,
                root_value=root_value,
                query_parser=query_parser,
                query_document=query_document,
                query_validator=query_validator,
                validation_rules=validation_rules,
                debug=debug,
                introspection=introspection,
                logger=logger,
                error_formatter=error_formatter,
            )

            if not success:
                # Handle subscription setup errors
                if not isinstance(results, list):
                    error_payload = cast(list[dict], [results])
                else:
                    error_payload = results

                yield SubscriptionEvent(
                    event_type=SubscriptionEventType.ERROR,
                    result=ExecutionResult(
                        errors=[
                            GraphQLError(message=cast(str, error.get("message", "")))
                            for error in error_payload
                        ]
                    ),
                )
            else:
                results = cast(AsyncGenerator[ExecutionResult, None], results)
                try:
                    async for result in results:
                        yield SubscriptionEvent(
                            event_type=SubscriptionEventType.NEXT,
                            result=result,
                        )
                except (Exception, GraphQLError) as error:
                    if not isinstance(error, GraphQLError):
                        error = GraphQLError(str(error), original_error=error)
                        log_error(error, logger)
                    yield SubscriptionEvent(
                        event_type=SubscriptionEventType.ERROR,
                        result=ExecutionResult(errors=[error]),
                    )
        except GraphQLError as error:
            log_error(error, logger)
            yield SubscriptionEvent(
                event_type=SubscriptionEventType.ERROR,
                result=ExecutionResult(errors=[error]),
            )
        yield SubscriptionEvent(event_type=SubscriptionEventType.COMPLETE)

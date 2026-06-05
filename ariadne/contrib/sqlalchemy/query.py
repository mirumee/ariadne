import inspect
from collections.abc import Sequence
from typing import Any

from graphql import GraphQLList, GraphQLNonNull, GraphQLObjectType, GraphQLSchema
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from ...objects import QueryType
from .objects import SQLAlchemyObjectType
from .utils import auto_eager_load


class SQLAlchemyQueryType(QueryType):
    """
    A custom Query type that automatically binds SQLAlchemy resolvers
    by inspecting the GraphQLSchema during the make_executable_schema build phase.
    """

    def __init__(
        self,
        object_types: Sequence[SQLAlchemyObjectType],
    ):
        super().__init__()
        self.object_types = {ot.name: ot for ot in object_types}
        self._object_types_by_model = {ot.model: ot for ot in object_types}

    @staticmethod
    def get_session_from_context(context: Any) -> Session | AsyncSession:
        try:
            return context["session"]
        except KeyError:
            raise RuntimeError("Session not found in context under key 'session'")

    def bind_to_schema(self, schema: GraphQLSchema) -> None:
        graphql_type = schema.type_map.get(self.name)
        if not isinstance(graphql_type, GraphQLObjectType):
            super().bind_to_schema(schema)
            return

        for field_name, field_def in graphql_type.fields.items():
            is_list = False
            unwrapped_type = field_def.type

            while isinstance(unwrapped_type, (GraphQLList, GraphQLNonNull)):
                if isinstance(unwrapped_type, GraphQLList):
                    is_list = True
                unwrapped_type = unwrapped_type.of_type

            type_name = getattr(unwrapped_type, "name", None)

            if type_name in self.object_types and field_name not in self._resolvers:
                obj_type = self.object_types[type_name]
                self.set_field(
                    field_name, self._create_auto_resolver(obj_type, is_list)
                )

        super().bind_to_schema(schema)

    def _create_auto_resolver(self, obj_type: SQLAlchemyObjectType, return_list: bool):
        def auto_resolve(obj: Any, info: Any, **kwargs: Any):
            session = self.get_session_from_context(info.context)

            model = obj_type.model
            stmt = obj_type.get_base_query(info, **kwargs)

            stmt = auto_eager_load(
                stmt,
                info,
                model,
                strategies=obj_type.strategies,
                aliases=obj_type.aliases,
                max_depth=obj_type.max_depth,
                type_registry=self._object_types_by_model,
            )

            mapper = sa_inspect(model)
            for key, value in kwargs.items():
                db_col_name = obj_type.aliases.get(key, key)
                if db_col_name in mapper.columns:
                    stmt = stmt.where(getattr(model, db_col_name) == value)

            result = session.execute(stmt)
            if inspect.isawaitable(result):

                async def await_result(awaitable_result: Any) -> Any:
                    r = await awaitable_result
                    if return_list:
                        return r.scalars().unique().all()
                    return r.scalars().first()

                return await_result(result)

            if return_list:
                return result.scalars().unique().all()
            return result.scalars().first()

        return auto_resolve

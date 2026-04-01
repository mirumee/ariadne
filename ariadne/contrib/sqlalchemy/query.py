from collections.abc import Sequence
from typing import Any

from graphql import GraphQLList, GraphQLNonNull, GraphQLObjectType, GraphQLSchema

from ...objects import ObjectType
from .objects import SQLAlchemyObjectType
from .utils import auto_eager_load


class SQLAlchemyQueryType(ObjectType):
    """
    A custom Query type that automatically binds SQLAlchemy resolvers
    by inspecting the GraphQLSchema during the make_executable_schema build phase.
    """

    def __init__(
        self,
        name: str,
        object_types: Sequence[SQLAlchemyObjectType],
        *,
        session_key: str = "session",
    ):
        super().__init__(name)
        self.object_types = {ot.name: ot for ot in object_types}
        self.session_key = session_key

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
        async def auto_resolve(obj: Any, info: Any, **kwargs: Any):
            session = info.context.get(self.session_key)
            if session is None:
                raise RuntimeError(
                    f"Session not found in context under key '{self.session_key}'"
                )

            model = obj_type.model
            stmt = obj_type.get_base_query(info, **kwargs)

            stmt = auto_eager_load(
                stmt,
                info,
                model,
                strategies=obj_type.strategies,
                aliases=obj_type.aliases,
                max_depth=obj_type.max_depth,
            )

            for key, value in kwargs.items():
                db_col_name = obj_type.aliases.get(key, key)
                if hasattr(model, db_col_name):
                    stmt = stmt.where(getattr(model, db_col_name) == value)

            result = await session.execute(stmt)

            if return_list:
                return result.scalars().unique().all()
            return result.scalars().first()

        return auto_resolve

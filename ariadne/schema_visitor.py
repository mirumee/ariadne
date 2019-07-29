from types import FunctionType
from typing import Any, Callable, Dict, List, Mapping, Type, TypeVar, Union, cast

from graphql import value_from_ast_untyped
from graphql.execution.values import get_argument_values
from graphql.language import DirectiveLocation
from graphql.type import (
    GraphQLArgument,
    GraphQLDirective,
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLField,
    GraphQLInputField,
    GraphQLInputObjectType,
    GraphQLInterfaceType,
    GraphQLNamedType,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLSchema,
    GraphQLUnionType,
)
from typing_extensions import Protocol

VisitableSchemaType = Union[
    GraphQLSchema,
    GraphQLObjectType,
    GraphQLInterfaceType,
    GraphQLInputObjectType,
    GraphQLNamedType,
    GraphQLScalarType,
    GraphQLField,
    GraphQLArgument,
    GraphQLUnionType,
    GraphQLEnumType,
    GraphQLEnumValue,
]
V = TypeVar("V")
IndexedObject = Union[Dict[str, V], List[V]]


Callback = Callable[..., Any]


def each(list_or_dict: IndexedObject, callback: Callback):
    if isinstance(list_or_dict, List):
        for value in list_or_dict:
            callback(value)
    else:
        for key, value in list_or_dict.items():
            callback(value, key)


def update_each_key(list_or_dict: IndexedObject, callback: Callback):
    """
    The callback can return None to leave the key untouched, False to remove
    the key from the array or object, or a non-null V to replace the value.
    """

    if isinstance(list_or_dict, List):
        # TODO: This branch of if could possibly be removed. graphql-core seems to be
        # always returning dicts
        indexes_to_remove: List[int] = []
        for i, value in enumerate(list_or_dict):
            result = callback(value)
            if result is False:
                indexes_to_remove.append(i)
            elif result is None:
                continue
            else:
                list_or_dict[i] = result
        list_or_dict[:] = [
            v for i, v in enumerate(list_or_dict) if i not in indexes_to_remove
        ]
    else:
        keys_to_remove: List[str] = []

        for key, value in list_or_dict.items():
            result = callback(value, key)
            if result is False:
                keys_to_remove.append(key)
            elif result is None:
                continue
            else:
                list_or_dict[key] = result
        for k in keys_to_remove:
            list_or_dict.pop(k)


class SchemaVisitor(Protocol):
    @classmethod
    def implements_visitor_method(cls, method_name: str):
        if not method_name.startswith("visit_"):
            return False

        method = getattr(cls, method_name)
        if type(method) is not FunctionType:
            return False

        if cls.__name__ == "SchemaVisitor":
            # The SchemaVisitor class implements every visitor method.
            return True

        if method.__qualname__.startswith("SchemaVisitor"):
            #  If this.prototype[method_name] was just inherited from SchemaVisitor,
            #  then this class does not really implement the method.
            return False

        return True

    def visit_schema(self, schema: GraphQLSchema) -> None:
        ...

    def visit_scalar(self, scalar: GraphQLScalarType) -> GraphQLScalarType:
        ...

    def visit_object(self, object_: GraphQLObjectType) -> GraphQLObjectType:
        ...

    def visit_field_definition(
        self,
        field: GraphQLField,
        object_type: Union[GraphQLObjectType, GraphQLInterfaceType],
    ) -> GraphQLField:
        ...

    def visit_argument_definition(
        self,
        argument: GraphQLArgument,
        field: GraphQLField,
        object_type: Union[GraphQLObjectType, GraphQLInterfaceType],
    ) -> GraphQLArgument:
        ...

    def visit_interface(self, iface: GraphQLInterfaceType) -> GraphQLInterfaceType:
        ...

    def visit_union(self, union: GraphQLUnionType) -> GraphQLUnionType:
        ...

    def visit_enum(self, type_: GraphQLEnumType) -> GraphQLEnumType:
        ...

    def visit_enum_value(
        self, value: GraphQLEnumValue, enum_type: GraphQLEnumType
    ) -> GraphQLEnumValue:
        ...

    def visit_input_object(
        self, object_: GraphQLInputObjectType
    ) -> GraphQLInputObjectType:
        ...

    def visit_input_field_definition(
        self, field: GraphQLInputField, object_type: GraphQLInputObjectType
    ) -> GraphQLInputField:
        ...


def visit_schema(
    schema: GraphQLSchema,
    visitor_selector: Callable[
        [VisitableSchemaType, str], List["SchemaDirectiveVisitor"]
    ],
) -> GraphQLSchema:
    """
    Helper function that calls visitor_selector and applies the resulting
    visitors to the given type, with arguments [type, ...args].
    """

    def call_method(
        method_name: str, type_: VisitableSchemaType, *args: Any
    ) -> VisitableSchemaType:
        for visitor in visitor_selector(type_, method_name):

            # TODO needs improvements to remove nodes. Since python does not
            # have 'undefined', False value is chosen for removal. Still more
            # clarification is needed. Maybe return a tuple instead? but that
            # would have an effect on the visitor methods' signature too.
            new_type = getattr(visitor, method_name)(type_, *args)

            if new_type is None:
                # Keep going without modifying type.
                continue

            if method_name == "visit_schema" or isinstance(type_, GraphQLSchema):
                raise Exception(
                    f"Method {method_name} cannot replace schema with {new_type}"
                )

            if new_type is False:
                # This does not make much sense in python
                # Stop the loop and return null form call_method, which will cause
                # the type to be removed from the schema.
                type_ = new_type
                break

            # Update type to the new type returned by the visitor method, so that
            # later directives will see the new type, and call_method will return
            # the final type.
            type_ = new_type

        # If there were no directives for this type object, or if all visitor
        # methods returned nothing, type will be returned unmodified.
        return type_

    def visit(type_: VisitableSchemaType) -> VisitableSchemaType:
        """
        Recursive helper function that calls any appropriate visitor methods for
        each object in the schema, then traverses the object's children (if any).
        """
        if isinstance(type_, GraphQLSchema):
            # Unlike the other types, the root GraphQLSchema object cannot be
            # replaced by visitor methods, because that would make life very hard
            # for SchemaVisitor subclasses that rely on the original schema object.
            call_method("visit_schema", type_)

            def _start(named_type, type_name):
                if not type_name.startswith("__"):
                    visit(named_type)

            update_each_key(type_.type_map, _start)

            return type_

        if isinstance(type_, GraphQLObjectType):
            # Note that call_method('visitObject', type) may not actually call any
            # methods, if there are no @directive annotations associated with this
            # type, or if this SchemaDirectiveVisitor subclass does not override
            # the visitObject method.
            new_object = cast(GraphQLObjectType, call_method("visit_object", type_))
            if new_object:
                visit_fields(new_object)

            return new_object

        if isinstance(type_, GraphQLInterfaceType):
            new_interface = cast(
                GraphQLInterfaceType, call_method("visit_interface", type_)
            )
            if new_interface:
                visit_fields(new_interface)

            return new_interface

        if isinstance(type_, GraphQLInputObjectType):
            new_input_object = cast(
                GraphQLInputObjectType, call_method("visit_input_object", type_)
            )

            if new_input_object:
                update_each_key(
                    new_input_object.fields,
                    lambda field, n: call_method(
                        "visit_input_field_definition", field, new_input_object
                    ),
                )

            return new_input_object

        if isinstance(type_, GraphQLScalarType):
            return call_method("visit_scalar", type_)

        if isinstance(type_, GraphQLUnionType):
            return call_method("visit_union", type_)

        if isinstance(type_, GraphQLEnumType):
            new_enum = cast(GraphQLEnumType, call_method("visit_enum", type_))

            if new_enum:
                update_each_key(
                    new_enum.values,
                    lambda value, n=new_enum: call_method("visit_enum_value", value, n),
                )

            return new_enum

        raise Exception(f"Unexpected schema type: {type}")

    def visit_fields(type_: Union[GraphQLObjectType, GraphQLInterfaceType]):
        def _update_fields(field, _):
            # It would be nice if we could call visit(field) recursively here, but
            # GraphQLField is merely a type, not a value that can be detected using
            # an instanceof check, so we have to visit the fields in this lexical
            # context, so that TypeScript can validate the call to
            # visit_field_definition.
            new_field = call_method("visit_field_definition", field, type_)
            # While any field visitor needs a reference to the field object, some
            # field visitors may also need to know the enclosing (parent) type,
            # perhaps to determine if the parent is a GraphQLObjectType or a
            # GraphQLInterfaceType. To obtain a reference to the parent, a
            # visitor method can have a second parameter, which will be reeferring
            # to the parent.

            if new_field and new_field.args:
                update_each_key(
                    new_field.args,
                    lambda arg, _: call_method(
                        "visit_argument_definition", arg, new_field, type_
                    ),
                )

            return new_field

        update_each_key(type_.fields, _update_fields)

    visit(schema)

    # Return the original schema for convenience, even though it cannot have
    # been replaced or removed by the code above.
    return schema


def directive_location_to_visitor_method_name(loc: DirectiveLocation):
    """
    Convert a string like "FIELD_DEFINITION" to "visit_field_definition".
    """
    return "visit_" + loc.name.lower()


class SchemaDirectiveVisitor(SchemaVisitor):
    def __init__(self, name, args, visited_type, schema, context):
        self.name = name
        self.args = args
        self.visited_type = visited_type
        self.schema = schema
        self.context = context

    @classmethod
    def get_directive_declaration(cls, directive_name: str, schema: GraphQLSchema):
        return schema.get_directive(directive_name)

    @classmethod
    def get_declared_directives(
        cls,
        schema: GraphQLSchema,
        directive_visitors: Dict[str, Type["SchemaDirectiveVisitor"]],
    ):
        declared_directives: Dict[str, GraphQLDirective] = {}

        def _add_directive(decl):
            declared_directives[decl.name] = decl

        each(schema.directives, _add_directive)

        #  If the visitor subclass overrides getDirectiveDeclaration, and it
        #  returns a non-null GraphQLDirective, use that instead of any directive
        #  declared in the schema itself. Reasoning: if a SchemaDirectiveVisitor
        #  goes to the trouble of implementing getDirectiveDeclaration, it should
        #  be able to rely on that implementation.
        def _get_overriden_directive(visitor_class, directive_name):
            decl = visitor_class.get_directive_declaration(directive_name, schema)
            if decl:
                declared_directives[directive_name] = decl

        each(directive_visitors, _get_overriden_directive)

        def _rest(decl, name):
            if not name in directive_visitors:
                #  SchemaDirectiveVisitors.visitSchemaDirectives might be called
                #  multiple times with partial directive_visitors maps, so it's not
                #  necessarily an error for directive_visitors to be missing an
                #  implementation of a directive that was declared in the schema.
                return

            visitor_class = directive_visitors[name]

            def _location_check(loc):
                visitor_method_name = directive_location_to_visitor_method_name(loc)

                if SchemaVisitor.implements_visitor_method(
                    visitor_method_name
                ) and not visitor_class.implements_visitor_method(visitor_method_name):
                    #  While visitor subclasses may implement extra visitor methods,
                    #  it's definitely a mistake if the GraphQLDirective declares itself
                    #  applicable to certain schema locations, and the visitor subclass
                    #  does not implement all the corresponding methods.
                    raise Exception(
                        f"SchemaDirectiveVisitor for @${name} must implement ${visitor_method_name} method"
                    )

            each(decl.locations, _location_check)

        each(declared_directives, _rest)

        return declared_directives

    @classmethod
    def visit_schema_directives(
        cls,
        schema: GraphQLSchema,
        directive_visitors: Dict[str, Type["SchemaDirectiveVisitor"]],
    ) -> Mapping[str, List["SchemaDirectiveVisitor"]]:
        declared_directives = cls.get_declared_directives(schema, directive_visitors)

        #  Map from directive names to lists of SchemaDirectiveVisitor instances
        #  created while visiting the schema.
        created_visitors: Dict[str, List["SchemaDirectiveVisitor"]] = {
            k: [] for k in directive_visitors
        }

        def _visitorSelector(
            type_: VisitableSchemaType, methodName: str
        ) -> List["SchemaDirectiveVisitor"]:
            visitors: List["SchemaDirectiveVisitor"] = []
            directive_nodes = type_.ast_node.directives if type_.ast_node else None
            if directive_nodes is None:
                return visitors

            for directive_node in directive_nodes:
                directive_name = directive_node.name.value
                if directive_name not in directive_visitors:
                    return []

                visitor_class = directive_visitors[directive_name]

                #  Avoid creating visitor objects if visitor_class does not override
                #  the visitor method named by methodName.
                if not visitor_class.implements_visitor_method(methodName):
                    return []

                decl = declared_directives[directive_name]

                args: Dict[str, Any] = {}

                if decl:
                    #  If this directive was explicitly declared, use the declared
                    #  argument types (and any default values) to check, coerce, and/or
                    #  supply default values for the given arguments.
                    args = get_argument_values(decl, directive_node)
                else:
                    #  If this directive was not explicitly declared, just convert the
                    #  argument nodes to their corresponding JavaScript values.
                    for arg in directive_node.arguments:
                        args[arg.name.value] = value_from_ast_untyped(arg.value)

                #  As foretold in comments near the top of the visitSchemaDirectives
                #  method, this is where instances of the SchemaDirectiveVisitor class
                #  get created and assigned names. While subclasses could override the
                #  constructor method, the constructor is marked as protected, so
                #  these are the only arguments that will ever be passed.
                visitors.append(visitor_class(directive_name, args, type_, schema, {}))

            for visitor in visitors:
                created_visitors[visitor.name].append(visitor)

            return visitors

        visit_schema(schema, _visitorSelector)

        #  Automatically update any references to named schema types replaced
        #  during the traversal, so implementors don't have to worry about that.
        # TODO heal_schema(schema)

        return created_visitors

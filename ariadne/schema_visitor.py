from types import FunctionType
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

from graphql import is_named_type, value_from_ast_untyped
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
    GraphQLList,
    GraphQLNamedType,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLSchema,
    GraphQLUnionType,
)
from typing_extensions import Literal, Protocol

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
V = TypeVar("V", bound=VisitableSchemaType)
VisitableMap = Dict[str, V]
IndexedObject = Union[VisitableMap, Tuple[V, ...]]


Callback = Callable[..., Any]


def each(tuple_or_dict: IndexedObject, callback: Callback):
    if isinstance(tuple_or_dict, tuple):
        for value in tuple_or_dict:
            callback(value)
    else:
        for key, value in tuple_or_dict.items():
            callback(value, key)


def update_each_key(object_map: VisitableMap, callback: Callback):
    """
    The callback can return None to leave the key untouched, False to remove
    the key from the array or object, or a non-null V to replace the value.
    """

    keys_to_remove: List[str] = []

    for key, value in object_map.copy().items():
        result = callback(value, key)
        if result is False:
            keys_to_remove.append(key)
        elif result is None:
            continue
        else:
            object_map[key] = result
    for k in keys_to_remove:
        object_map.pop(k)


class SchemaVisitor(Protocol):
    @classmethod
    def implements_visitor_method(cls, method_name: str):
        if not method_name.startswith("visit_"):
            return False

        try:
            method = getattr(cls, method_name)
        except AttributeError:
            return False

        if not isinstance(method, FunctionType):
            return False

        if cls.__name__ == "SchemaVisitor":
            # The SchemaVisitor class implements every visitor method.
            return True

        if method.__qualname__.startswith("SchemaVisitor"):
            #  When SchemaVisitor subclass does not really implement the method.
            return False

        return True

    # pylint: disable=unused-argument
    def visit_schema(self, schema: GraphQLSchema) -> None:
        pass

    def visit_scalar(self, scalar: GraphQLScalarType) -> GraphQLScalarType:
        pass

    def visit_object(self, object_: GraphQLObjectType) -> GraphQLObjectType:
        pass

    def visit_field_definition(
        self,
        field: GraphQLField,
        object_type: Union[GraphQLObjectType, GraphQLInterfaceType],
    ) -> GraphQLField:
        pass

    def visit_argument_definition(
        self,
        argument: GraphQLArgument,
        field: GraphQLField,
        object_type: Union[GraphQLObjectType, GraphQLInterfaceType],
    ) -> GraphQLArgument:
        pass

    def visit_interface(self, interface: GraphQLInterfaceType) -> GraphQLInterfaceType:
        pass

    def visit_union(self, union: GraphQLUnionType) -> GraphQLUnionType:
        pass

    def visit_enum(self, type_: GraphQLEnumType) -> GraphQLEnumType:
        pass

    def visit_enum_value(
        self, value: GraphQLEnumValue, enum_type: GraphQLEnumType
    ) -> GraphQLEnumValue:
        pass

    def visit_input_object(
        self, object_: GraphQLInputObjectType
    ) -> GraphQLInputObjectType:
        pass

    def visit_input_field_definition(
        self, field: GraphQLInputField, object_type: GraphQLInputObjectType
    ) -> GraphQLInputField:
        pass


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
    ) -> Union[VisitableSchemaType, Literal[False]]:
        for visitor in visitor_selector(type_, method_name):

            new_type = getattr(visitor, method_name)(type_, *args)
            if new_type is None:
                # Keep going without modifying type.
                continue

            if method_name == "visit_schema" or isinstance(type_, GraphQLSchema):
                raise ValueError(
                    f"Method {method_name} cannot replace schema with {new_type}"
                )

            if new_type is False:
                # Stop the loop and return False form call_method, which will cause
                # the type to be removed from the schema.
                del type_
                return False

            # Update type to the new type returned by the visitor method, so that
            # later directives will see the new type, and call_method will return
            # the final type.
            type_ = new_type

        # If there were no directives for this type object, or if all visitor
        # methods returned nothing, type will be returned unmodified.
        return type_

    def visit(  # pylint: disable=too-many-return-statements
        type_: VisitableSchemaType,
    ) -> Union[VisitableSchemaType, Literal[False]]:
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
            # Note that call_method('visit_object', type_) may not actually call any
            # methods, if there are no @directive annotations associated with this
            # type, or if this SchemaDirectiveVisitor subclass does not override
            # the visit_object method.
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
                    lambda value, name: call_method("visit_enum_value", value, name),
                )

            return new_enum

        raise ValueError(f"Unexpected schema type: {type_}")

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

        #  If the visitor subclass overrides get_directive_declaration, and it
        #  returns a non-null GraphQLDirective, use that instead of any directive
        #  declared in the schema itself. Reasoning: if a SchemaDirectiveVisitor
        #  goes to the trouble of implementing get_directive_declaration, it should
        #  be able to rely on that implementation.
        def _get_overriden_directive(visitor_class, directive_name):
            decl = visitor_class.get_directive_declaration(directive_name, schema)
            if decl:
                declared_directives[directive_name] = decl

        each(directive_visitors, _get_overriden_directive)

        def _rest(decl, name):
            if not name in directive_visitors:
                #  SchemaDirectiveVisitors.visit_schema_directives might be called
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
                    raise ValueError(
                        f"SchemaDirectiveVisitor for @{name} must"
                        f"implement {visitor_method_name} method"
                    )

            each(decl.locations, _location_check)

        each(declared_directives, _rest)

        return declared_directives

    @classmethod
    def visit_schema_directives(
        cls,
        schema: GraphQLSchema,
        directive_visitors: Dict[str, Type["SchemaDirectiveVisitor"]],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Mapping[str, List["SchemaDirectiveVisitor"]]:
        declared_directives = cls.get_declared_directives(schema, directive_visitors)

        #  Map from directive names to lists of SchemaDirectiveVisitor instances
        #  created while visiting the schema.
        created_visitors: Dict[str, List["SchemaDirectiveVisitor"]] = {
            k: [] for k in directive_visitors
        }

        def _visitor_selector(
            type_: VisitableSchemaType, method_name: str
        ) -> List["SchemaDirectiveVisitor"]:
            visitors: List["SchemaDirectiveVisitor"] = []
            directive_nodes = type_.ast_node.directives if type_.ast_node else None
            if directive_nodes is None:
                return visitors

            for directive_node in directive_nodes:
                directive_name = directive_node.name.value
                if directive_name not in directive_visitors:
                    continue

                visitor_class = directive_visitors[directive_name]

                #  Avoid creating visitor objects if visitor_class does not override
                #  the visitor method named by method_name.
                if not visitor_class.implements_visitor_method(method_name):
                    continue

                decl = declared_directives[directive_name]

                args: Dict[str, Any] = {}

                if decl:
                    #  If this directive was explicitly declared, use the declared
                    #  argument types (and any default values) to check, coerce, and/or
                    #  supply default values for the given arguments.
                    args = get_argument_values(decl, directive_node)
                else:
                    #  If this directive was not explicitly declared, just convert the
                    #  argument nodes to their corresponding values.
                    for arg in directive_node.arguments:
                        args[arg.name.value] = value_from_ast_untyped(arg.value)

                #  As foretold in comments near the top of the visit_schema_directives
                #  method, this is where instances of the SchemaDirectiveVisitor class
                #  get created and assigned names. While subclasses could override the
                #  constructor method, the constructor is marked as protected, so
                #  these are the only arguments that will ever be passed.
                visitors.append(
                    visitor_class(directive_name, args, type_, schema, context)
                )

            for visitor in visitors:
                created_visitors[visitor.name].append(visitor)

            return visitors

        visit_schema(schema, _visitor_selector)

        # Automatically update any references to named schema types replaced
        # during the traversal, so implementors don't have to worry about that.
        heal_schema(schema)

        return created_visitors


NamedTypeMap = Dict[str, GraphQLNamedType]


def heal_schema(schema: GraphQLSchema) -> GraphQLSchema:
    def heal(type_: VisitableSchemaType):
        if isinstance(type_, GraphQLSchema):
            original_type_map: NamedTypeMap = type_.type_map
            actual_named_type_map: NamedTypeMap = {}

            def _heal_original(named_type, type_name):
                if type_name.startswith("__"):
                    return None

                actual_name = named_type.name
                if actual_name.startswith("__"):
                    return None

                if actual_name in actual_named_type_map:
                    raise ValueError(f"Duplicate schema type name {actual_name}")

                actual_named_type_map[actual_name] = named_type

                # Note: we are deliberately leaving named_type in the schema by its
                # original name (which might be different from actual_name), so that
                # references by that name can be healed.
                return None

            # If any of the .name properties of the GraphQLNamedType objects in
            # schema.type_map have changed, the keys of the type map need to
            # be updated accordingly.
            each(original_type_map, _heal_original)

            # Now add back every named type by its actual name.
            def _add_back(named_type, type_name):
                original_type_map[type_name] = named_type

            each(actual_named_type_map, _add_back)

            # Directive declaration argument types can refer to named types.
            def _heal_directive_declaration(decl: GraphQLDirective):
                def _heal_arg(arg, _):
                    arg.type = heal_type(arg.type)

                if decl.args:
                    each(decl.args, _heal_arg)

            each(type_.directives, _heal_directive_declaration)

            def _heal_type(named_type, type_name):
                if not type_name.startswith("__"):
                    heal(named_type)

            each(original_type_map, _heal_type)

            # Dangling references to renamed types should remain in the schema
            # during healing, but must be removed now, so that the following
            # invariant holds for all names: schema.get_type(name).name === name
            def _remove_dangling_references(_, type_name):
                if (
                    not type_name.startswith("__")
                    and type_name not in actual_named_type_map
                ):
                    return False
                return None

            update_each_key(original_type_map, _remove_dangling_references)

        elif isinstance(type_, GraphQLObjectType):
            heal_fields(type_)
            each(type_.interfaces, heal)

        elif isinstance(type_, GraphQLInterfaceType):
            heal_fields(type_)

        elif isinstance(type_, GraphQLInputObjectType):

            def _heal_field_type(field, _):
                field.type = heal_type(field.type)

            each(type_.fields, _heal_field_type)

        elif isinstance(type_, GraphQLScalarType):
            # Nothing to do.
            pass

        elif isinstance(type_, GraphQLUnionType):
            each(type_.types, heal_type)

        elif isinstance(type_, GraphQLEnumType):
            # Nothing to do.
            pass

        else:
            raise ValueError(f"Unexpected schema type: {type_}")

    def heal_fields(type_: Union[GraphQLObjectType, GraphQLInterfaceType]):
        def _heal_arg(arg, _):
            arg.type = heal_type(arg.type)

        def _heal_field(field, _):
            field.type = heal_type(field.type)
            if field.args:
                each(field.args, _heal_arg)

        each(type_.fields, _heal_field)

    def heal_type(
        type_: Union[GraphQLList, GraphQLNamedType, GraphQLNonNull]
    ) -> Union[GraphQLList, GraphQLNamedType, GraphQLNonNull]:
        # Unwrap the two known wrapper types
        if isinstance(type_, GraphQLList):
            type_ = GraphQLList(heal_type(type_.of_type))
        elif isinstance(type_, GraphQLNonNull):
            type_ = GraphQLNonNull(heal_type(type_.of_type))
        elif is_named_type(type_):
            # If a type annotation on a field or an argument or a union member is
            # any `GraphQLNamedType` with a `name`, then it must end up identical
            # to `schema.get_type(name)`, since `schema.type_map` is the source
            # of truth for all named schema types.
            named_type = cast(GraphQLNamedType, type_)
            official_type = schema.get_type(named_type.name)
            if official_type and named_type != official_type:
                return official_type

        return type_

    heal(schema)
    return schema

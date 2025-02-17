"""Introspect public API and generate reference from it."""

import ast
import os
import re
from dataclasses import dataclass
from importlib import import_module
from textwrap import dedent
from typing import Union

import ariadne
from ariadne import asgi, constants, exceptions, types, wsgi
from ariadne.asgi import handlers as asgi_handlers

GRAPHQL_SCHEMA_URL = "https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema"

URL_KEYWORDS = [
    (r"(`?GraphQLSchema`?)", GRAPHQL_SCHEMA_URL),
    (r"(graphql schemas?)", GRAPHQL_SCHEMA_URL),
    (r"(`?bindables?`?)", "bindables.md"),
    (r"(`ContextValue`)", "types-reference.md#contextvalue"),
    (r"(`ErrorFormatter`)", "types-reference.md#errorformatter"),
    (
        r"(`GraphQLHTTPHandler`)",
        "asgi-handlers-reference.md#graphqlhttphandler",
    ),
    (
        r"(`GraphQLWebsocketHandler`)",
        "asgi-handlers-reference.md#graphqlwebsockethandler",
    ),
    (r"(`Explorer`)", "explorers.md"),
    (r"(`Extensions`)", "types-reference.md#extensions"),
    (r"(`ExtensionList`)", "types-reference.md#extensionlist"),
    (r"(`GraphQLResult`)", "types-reference.md#graphqlresult"),
    (r"(`Middlewares`)", "types-reference.md#middlewares"),
    (r"(`MiddlewareList`)", "types-reference.md#middlewarelist"),
    (r"(`QueryParser`)", "types-reference.md#queryparser"),
    (r"(`RootValue`)", "types-reference.md#rootvalue"),
    (r"(`ValidationRules`)", "types-reference.md#validationrules"),
    (r"(`Operation`)", "types-reference.md#operation"),
    (r"(`OnConnect`)", "types-reference.md#onconnect"),
    (r"(`OnDisconnect`)", "types-reference.md#ondisconnect"),
    (r"(`OnOperation`)", "types-reference.md#onoperation"),
    (r"(`OnComplete`)", "types-reference.md#oncomplete"),
    (
        r"(`GraphQLHTTPHandler`)",
        "asgi-handlers-reference.md#GraphQLHTTPHandler",
    ),
    (
        r"(`GraphQLWebsocketHandler`)",
        "asgi-handlers-reference.md#graphqlwebsockethandler",
    ),
    (
        r"(`GraphQLWSHandler`)",
        "asgi-handlers-reference.md#graphqlwshandler",
    ),
    (
        r"(connection scope)",
        "https://asgi.readthedocs.io/en/latest/specs/main.html#connection-scope",
    ),
]


def main():
    if not os.path.isdir("docs"):
        os.mkdir("docs")

    generate_ariadne_reference()
    generate_asgi_reference()
    generate_asgi_handlers_reference()
    generate_constants_reference()
    generate_exceptions_reference()
    generate_types_reference()
    generate_wsgi_reference()


def generate_ariadne_reference():
    text = dedent(
        """
        ---
        id: api-reference
        title: API reference
        sidebar_label: ariadne
        ---

        Following items are importable directly from `ariadne` package:
        """
    ).strip()

    reference_items = []

    all_names = sorted(ariadne.__all__)
    ast_definitions = get_all_ast_definitions(all_names, ariadne)

    for item_name in sorted(all_names):
        item_doc = f"## `{item_name}`"
        item_doc += "\n\n"

        if item_name in ast_definitions:
            item = getattr(ariadne, item_name)
            item_ast = ast_definitions[item_name]
            if isinstance(item_ast, ast.ClassDef):
                item_doc += get_class_reference(item, item_ast)
            if isinstance(item_ast, (ast.AsyncFunctionDef, ast.FunctionDef)):
                item_doc += get_function_reference(item, item_ast)
            if isinstance(item_ast, ast.Assign):
                item_doc += get_varname_reference(
                    item, item_ast, ast_definitions.get(f"doc:{item_name}")
                )

            reference_items.append(item_doc)

    text += "\n\n\n"
    text += "\n\n\n- - - - -\n\n\n".join(reference_items)

    with open("docs/api-reference.md", "w+") as fp:
        fp.write(text.strip())


def generate_asgi_reference():
    text = dedent(
        """
        ---
        id: asgi-reference
        title: ASGI reference
        sidebar_label: ariadne.asgi
        ---

        The `ariadne.asgi` package exports the `GraphQL` ASGI application:
        """
    )

    reference_items = {}

    all_names = asgi.__all__
    ast_definitions = get_all_ast_definitions(all_names, asgi)

    for item_name in sorted(all_names):
        item_doc = f"## `{item_name}`"
        item_doc += "\n\n"

        if item_name in ast_definitions:
            item = getattr(asgi, item_name)
            item_ast = ast_definitions[item_name]
            if isinstance(item_ast, ast.ClassDef):
                item_doc += get_class_reference(item, item_ast)
            if isinstance(item_ast, (ast.AsyncFunctionDef, ast.FunctionDef)):
                item_doc += get_function_reference(item, item_ast)
            if isinstance(item_ast, ast.Assign):
                item_doc += get_varname_reference(
                    item, item_ast, ast_definitions.get(f"doc:{item_name}")
                )

            reference_items[item_name] = item_doc

    text += "\n\n"
    text += reference_items.pop("GraphQL")
    text += "\n\n\n- - - - -\n\n\n"
    text += "`ariadne.asgi` package also reexports following names:"
    text += "\n\n"
    text += "\n".join(sorted([f"- `{name}`" for name in reference_items]))

    with open("docs/asgi-reference.md", "w+") as fp:
        fp.write(text.strip())


def generate_asgi_handlers_reference():
    text = dedent(
        """
        ---
        id: asgi-handlers-reference
        title: ASGI handlers reference
        sidebar_label: ariadne.asgi.handlers
        ---

        The `ariadne.asgi.handlers` package exports following 
        ASGI request handlers:
        """
    )

    reference_items = []

    all_names = asgi_handlers.__all__
    ast_definitions = get_all_ast_definitions(all_names, asgi_handlers)

    for item_name in sorted(all_names):
        item_doc = f"## `{item_name}`"
        item_doc += "\n\n"

        if item_name in ast_definitions:
            item = getattr(asgi_handlers, item_name)
            item_ast = ast_definitions[item_name]
            if isinstance(item_ast, ast.ClassDef):
                item_doc += get_class_reference(item, item_ast)
            if isinstance(item_ast, (ast.AsyncFunctionDef, ast.FunctionDef)):
                item_doc += get_function_reference(item, item_ast)
            if isinstance(item_ast, ast.Assign):
                item_doc += get_varname_reference(
                    item, item_ast, ast_definitions.get(f"doc:{item_name}")
                )

            reference_items.append(item_doc)

    text += "\n\n\n"
    text += "\n\n\n- - - - -\n\n\n".join(reference_items)

    with open("docs/asgi-handlers-reference.md", "w+") as fp:
        fp.write(text.strip())


def generate_constants_reference():
    text = dedent(
        """
        ---
        id: constants-reference
        title: Constants reference
        sidebar_label: ariadne.constants
        ---

        Following constants are importable from `ariadne.constants` module:
        """
    ).strip()

    reference_items = []

    all_names = [name for name in dir(constants) if not name.startswith("_")]
    ast_definitions = get_all_ast_definitions(all_names, constants)

    for item_name in sorted(all_names):
        item_doc = f"## `{item_name}`"
        item_doc += "\n\n"

        if item_name in ast_definitions:
            item = getattr(constants, item_name)
            item_ast = ast_definitions[item_name]
            if isinstance(item_ast, ast.ClassDef):
                continue

            item_doc += get_varname_reference(
                item, item_ast, ast_definitions.get(f"doc:{item_name}")
            )
            reference_items.append(item_doc)

    text += "\n\n\n"
    text += "\n\n\n- - - - -\n\n\n".join(reference_items)

    with open("docs/constants-reference.md", "w+") as fp:
        fp.write(text.strip())


def generate_exceptions_reference():
    text = dedent(
        """
        ---
        id: exceptions-reference
        title: Exceptions reference
        sidebar_label: ariadne.exceptions
        ---

        Ariadne defines some custom exception types that can be 
        imported from `ariadne.exceptions` module:
        """
    )

    reference_items = []

    all_names = [name for name in dir(exceptions) if not name.startswith("_")]
    ast_definitions = get_all_ast_definitions(all_names, exceptions)

    for item_name in sorted(all_names):
        if item_name not in ast_definitions:
            continue

        item_ast = ast_definitions[item_name]
        if not isinstance(item_ast, ast.ClassDef):
            continue

        item_doc = f"## `{item_name}`"
        item_doc += "\n\n"

        if item_name in ast_definitions:
            item = getattr(exceptions, item_name)
            item_doc += get_class_reference(item, item_ast)
            reference_items.append(item_doc)

    text += "\n\n\n"
    text += "\n\n\n- - - - -\n\n\n".join(reference_items)

    with open("docs/exceptions-reference.md", "w+") as fp:
        fp.write(text.strip())


def generate_types_reference():
    text = dedent(
        """
        ---
        id: types-reference
        title: Types reference
        sidebar_label: ariadne.types
        ---

        Ariadne uses [type annotations]
        (https://www.python.org/dev/peps/pep-0484/) in its codebase.

        Many parts of its API share or rely on common types, 
        importable from `ariadne.types` module:
        """
    )

    reference_items = []

    all_names = types.__all__
    ast_definitions = get_all_ast_definitions(all_names, types)

    for item_name in sorted(all_names):
        item_doc = f"## `{item_name}`"
        item_doc += "\n\n"

        if item_name in ast_definitions:
            item = getattr(types, item_name)
            item_ast = ast_definitions[item_name]
            if isinstance(item_ast, ast.ClassDef):
                item_doc += get_class_reference(item, item_ast)
            if isinstance(item_ast, (ast.AsyncFunctionDef, ast.FunctionDef)):
                item_doc += get_function_reference(item, item_ast)
            if isinstance(item_ast, ast.Assign):
                item_doc += get_varname_reference(
                    item, item_ast, ast_definitions.get(f"doc:{item_name}")
                )

            reference_items.append(item_doc)

    text += "\n\n\n"
    text += "\n\n\n- - - - -\n\n\n".join(reference_items)

    with open("docs/types-reference.md", "w+") as fp:
        fp.write(text.strip())


def generate_wsgi_reference():
    text = dedent(
        """
        ---
        id: wsgi-reference
        title: WSGI reference
        sidebar_label: ariadne.wsgi
        ---

        The `ariadne.wsgi` module exports the WSGI application and middleware:
        """
    )

    reference_items = []

    all_names = ["GraphQL", "GraphQLMiddleware", "FormData"]
    ast_definitions = get_all_ast_definitions(all_names, wsgi)

    if set(all_names) != set(wsgi.__all__):
        raise Exception(
            "'all_names' list in generate_wsgi_reference is outdated and "
            "needs manual update!"
        )

    for item_name in all_names:
        item_doc = f"## `{item_name}`"
        item_doc += "\n\n"

        if item_name in ast_definitions:
            item = getattr(wsgi, item_name)
            item_ast = ast_definitions[item_name]
            if isinstance(item_ast, ast.ClassDef):
                item_doc += get_class_reference(item, item_ast)
            if isinstance(item_ast, (ast.AsyncFunctionDef, ast.FunctionDef)):
                item_doc += get_function_reference(item, item_ast)
            if isinstance(item_ast, ast.Assign):
                item_doc += get_varname_reference(
                    item, item_ast, ast_definitions.get(f"doc:{item_name}")
                )

            reference_items.append(item_doc)

    text += "\n\n\n"
    text += "\n\n\n- - - - -\n\n\n".join(reference_items)

    with open("docs/wsgi-reference.md", "w+") as fp:
        fp.write(text.strip())


def get_all_ast_definitions(all_names, root_module):
    names_set = set(all_names)
    checked_modules = []
    definitions = {}

    def visit_node(ast_node, module):
        if isinstance(ast_node, ast.Module):
            for i, node in enumerate(ast_node.body):
                visit_node(node, module)

                # Extract documentation from prepending string
                if isinstance(node, ast.Assign) and i:
                    name = node.targets[0].id
                    previous_node = ast_node.body[i - 1]
                    if isinstance(previous_node, ast.Expr):
                        obj_name_key = f"doc:{name}"
                        if obj_name_key in definitions:
                            continue

                        node_extra_documentation = previous_node.value.value.strip()
                        definitions[obj_name_key] = node_extra_documentation

        elif isinstance(ast_node, ast.ImportFrom) and ast_node.level:
            if ast_node.module in checked_modules:
                return

            checked_modules.append(ast_node.module)

            imported_names = set([alias.name for alias in ast_node.names])
            if names_set.intersection(imported_names):
                import_name = get_import_name(module, ast_node.module, ast_node.level)
                module = import_module(import_name)
                with open(module.__file__) as fp:
                    module_ast = ast.parse(fp.read())
                    visit_node(module_ast, module)

        elif isinstance(
            ast_node, (ast.AsyncFunctionDef, ast.FunctionDef, ast.ClassDef)
        ):
            if ast_node.name in names_set:
                if ast_node.name not in definitions:
                    definitions[ast_node.name] = ast_node

        elif isinstance(ast_node, ast.Assign):
            name = ast_node.targets[0].id
            if name in names_set and name not in definitions:
                definitions[name] = ast_node

    with open(root_module.__file__) as fp:
        module_ast = ast.parse(fp.read())
        visit_node(module_ast, root_module)

    return definitions


def get_import_name(from_module, import_name, import_level):
    file_path = os.path.normpath(
        os.path.dirname(os.path.abspath(from_module.__file__))
    ).split(os.sep)

    while file_path.count("ariadne") > 1:
        file_path = file_path[file_path.index("ariadne") + 1 :]

    if import_level > 1:
        up_level = (import_level - 1) * -1
        file_path = file_path[:up_level]

    base_path = ".".join(file_path)
    return f"{base_path}.{import_name}"


def get_class_reference(obj, obj_ast: ast.ClassDef):  # noqa: C901
    reference = "```python\n"
    reference += f"class {obj_ast.name}"

    bases = [base.id for base in obj_ast.bases]
    if bases:
        reference += "({})".format(", ".join(bases))

    reference += ":\n    ...\n```"

    doc = parse_docstring(obj.__doc__)
    methods = get_class_methods(obj, obj_ast)
    constructor = methods.pop("__init__", None)

    if doc:
        if doc.lead:
            reference += "\n\n"
            reference += doc.lead

        for section in doc.sections:
            reference += "\n\n\n"
            reference += "##" + section

    if constructor:
        reference += "\n\n\n"
        reference += "### Constructor"
        reference += "\n\n"
        reference += constructor["code"]

        if constructor["doc"]:
            if constructor["doc"].lead:
                reference += "\n\n"
                reference += constructor["doc"].lead

            for section in constructor["doc"].sections:
                reference += "\n\n\n"
                reference += "###" + section

    if methods:
        methods_list = []

        for method_name, method in methods.items():
            method_reference = f"#### `{method_name}`"
            method_reference += "\n\n"
            method_reference += method["code"]

            if method["doc"]:
                if method["doc"].lead:
                    method_reference += "\n\n"
                    method_reference += method["doc"].lead

                for section in method["doc"].sections:
                    method_reference += "\n\n\n"
                    method_reference += "####" + section

                if method["doc"].examples:
                    method_reference += "\n\n\n####"
                    method_reference += "\n\n\n####".join(method["doc"].examples)

            methods_list.append(method_reference)

        reference += "\n\n\n"
        reference += "### Methods"
        reference += "\n\n"
        reference += "\n\n\n".join(methods_list)

    if doc and doc.examples:
        reference += "\n\n\n##"
        reference += "\n\n\n##".join(doc.examples)

    return reference


def get_class_methods(obj, obj_ast: ast.FunctionDef):
    methods = {}
    for node in obj_ast.body:
        if not isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
            continue

        if node.name.startswith("_") and not node.name.startswith("__"):
            continue

        code = "```python\n"
        code += "async " if isinstance(node, ast.AsyncFunctionDef) else ""
        code += f"def {node.name}"
        code += get_function_signature(node)
        code += ":"
        code += "\n    ..."
        code += "\n```"

        doc = parse_docstring(getattr(obj, node.name).__doc__, 1)

        methods[node.name] = {
            "code": code,
            "doc": doc,
        }

    return methods


def skip_init_method(obj_ast: ast.FunctionDef):
    if obj_ast.name != "__init__":
        return False

    if obj_ast.args.vararg or obj_ast.args.kwarg:
        return True

    args = len(obj_ast.args.args)
    args += len(obj_ast.args.posonlyargs)
    args += len(obj_ast.args.kwonlyargs)

    return args == 1


def get_function_reference(obj, obj_ast: Union[ast.AsyncFunctionDef, ast.FunctionDef]):
    reference = "```python\n"

    if isinstance(obj_ast, ast.AsyncFunctionDef):
        reference += "async "

    reference += f"def {obj_ast.name}"
    reference += get_function_signature(obj_ast)
    reference += ":\n"
    reference += "    ..."
    reference += "\n```"

    doc = parse_docstring(obj.__doc__)

    if doc:
        if doc.lead:
            reference += "\n\n"
            reference += doc.lead

        for section in doc.sections:
            reference += "\n\n\n"
            reference += "##" + section

        if doc.examples:
            reference += "\n\n\n##"
            reference += "\n\n\n##".join(doc.examples)

    return reference


def get_function_signature(obj_ast):  # noqa: C901
    returns = ast.unparse(obj_ast.returns) if obj_ast.returns else "None"

    params = []

    args_count = len(obj_ast.args.args)
    pargs_count = len(obj_ast.args.posonlyargs)
    defaults = obj_ast.args.defaults
    defaults_counts = len(defaults)
    kw_defaults = obj_ast.args.kw_defaults

    for i, arg in enumerate(obj_ast.args.posonlyargs):
        param = ast.unparse(arg)
        if defaults:
            index = defaults_counts - (pargs_count + args_count - i)
            try:
                if index >= 0:
                    default = defaults[index]
                    if default:
                        param += " = " + ast.unparse(default)
            except IndexError:
                pass
        params.append(param)

    if obj_ast.args.posonlyargs:
        params.append("/")

    for i, arg in enumerate(obj_ast.args.args):
        param = ast.unparse(arg)
        if defaults:
            index = defaults_counts - (args_count - i)
            try:
                if index >= 0:
                    default = defaults[index]
                    if default:
                        param += " = " + ast.unparse(default)
            except IndexError:
                pass
        params.append(param)

    if obj_ast.args.vararg:
        params.append("*" + ast.unparse(obj_ast.args.vararg))
    elif obj_ast.args.kwonlyargs:
        params.append("*")

    for index, arg in enumerate(obj_ast.args.kwonlyargs):
        param = ast.unparse(arg)
        if defaults:
            try:
                if index >= 0:
                    default = kw_defaults[index]
                    if default:
                        param += " = " + ast.unparse(default)
            except IndexError:
                pass
        params.append(param)

    if obj_ast.args.kwarg:
        params.append("**" + ast.unparse(obj_ast.args.kwarg))

    signature_str = "("

    params_str = ", ".join(params)
    if len(params_str) + len(signature_str) + len(returns) + len(obj_ast.name) < 70:
        signature_str += params_str
    else:
        params_str = ",\n    ".join(params)
        signature_str += f"\n    {params_str},\n"

    signature_str += ")"

    if obj_ast.name != "__init__":
        signature_str += f" -> {returns}"

    return signature_str


def get_varname_reference(obj, obj_ast, doc):
    reference = "```python\n"
    reference += ast.unparse(obj_ast)
    reference += "\n```"

    if doc:
        doc = parse_docstring(doc)

        reference += "\n\n"
        reference += doc.lead

        if doc.sections:
            reference += "\n\n\n##"
            reference += "\n\n\n##".join(doc.sections)

        if doc.examples:
            reference += "\n\n\n##"
            reference += "\n\n\n##".join(doc.examples)

    return reference


@dataclass
class ParsedDoc:
    lead: str
    sections: list[str]
    examples: list[str]


def parse_docstring(doc: Union[str, None], depth: int = 0) -> ParsedDoc:
    if not str(doc or "").strip():
        return

    doc = dedent(((depth + 1) * "    ") + doc)
    doc = collapse_lines(doc)
    doc = urlify_keywords(doc)

    lead = ""

    if "\n#" in doc:
        lead = doc[: doc.find("\n#")].strip()
        doc = doc[doc.find("\n#") :].strip()
    else:
        lead = doc
        doc = None

    if doc:
        sections = split_sections(doc)
    else:
        sections = []

    other_sections = []
    examples = []
    for section in sections:
        if section.lower().lstrip("# ").startswith("example"):
            examples.append(section)
        else:
            other_sections.append(section)

    return ParsedDoc(
        lead=lead,
        sections=other_sections,
        examples=examples,
    )


def collapse_lines(text: str) -> str:
    lines = []
    in_code = False
    for line in text.splitlines():
        if line.startswith("```"):
            in_code = not in_code

        if in_code:
            line = f"{line}\n"
        elif not line.endswith(" ") or line.strip() == ">":
            line = f"{line}\n"

        lines.append(line)

    return ("".join(lines)).strip()


def urlify_keywords(text: str) -> str:
    lines = []
    in_code = False
    for line in text.splitlines():
        if line.startswith("```"):
            in_code = not in_code

        if not in_code and not line.strip().startswith("#"):
            line = urlify_keywords_in_text(line)

        lines.append(line)

    return "\n".join(lines)


def urlify_keywords_in_text(text: str) -> str:
    for pattern, url in URL_KEYWORDS:
        text = re.sub(f"{pattern}", f"[\\1]({url})", text, flags=re.IGNORECASE)
    return text


def split_sections(text: str) -> list[str]:
    sections = []
    lines = []
    in_code = False
    for line in text.splitlines():
        if line.startswith("```"):
            in_code = not in_code

        if not in_code and line.startswith("#"):
            if lines:
                sections.append(("\n".join(lines)).strip())
                lines = []

        lines.append(line)

    if lines:
        sections.append(("\n".join(lines)).strip())

    return sections


if __name__ == "__main__":
    main()

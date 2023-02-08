"""Introspect public API and generate reference from it."""
import ast
import re
from dataclasses import dataclass
from importlib import import_module
from textwrap import dedent, indent

import ariadne
from ariadne import constants, exceptions


URL_KEYWORDS = [
    (
        r"(bindables?)",
        "bindables.md",
    ),
    (
        r"(graphql schemas?)",
        "https://graphql-core-3.readthedocs.io/en/latest/modules/type.html#graphql.type.GraphQLSchema",
    ),
]


def main():
    generate_ariadne_reference()
    generate_constants_reference()
    generate_exceptions_reference()


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

    for item_name in all_names:
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

    with open("api-reference.md", "w+") as fp:
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

    all_names = [name for name in dir(constants) if not name.startswith("_")]
    ast_definitions = get_all_ast_definitions(all_names, constants)

    for item_name in sorted(all_names):
        text += "\n\n\n"
        text += f"## `{item_name}`"
        text += "\n\n"

        if item_name in ast_definitions:
            item = getattr(constants, item_name)
            item_ast = ast_definitions[item_name]
            if isinstance(item_ast, ast.ClassDef):
                continue
        
            text += get_varname_reference(
                item, item_ast, ast_definitions.get(f"doc:{item_name}")
            )

    with open("constants-reference.md", "w+") as fp:
        fp.write(text.strip())


def generate_exceptions_reference():
    text = dedent(
        """
        ---
        id: exceptions-reference
        title: Exceptions reference
        sidebar_label: ariadne.exceptions
        ---

        Ariadne defines some custom exception types that can be imported from `ariadne.exceptions` module:
        """
    )

    all_names = [name for name in dir(exceptions) if not name.startswith("_")]
    ast_definitions = get_all_ast_definitions(all_names, exceptions)

    for item_name in sorted(all_names):
        if item_name not in ast_definitions:
            continue

        item_ast = ast_definitions[item_name]
        if not isinstance(item_ast, ast.ClassDef):
            continue

        text += "\n\n\n"
        text += f"## `{item_name}`"
        text += "\n\n"

        if item_name in ast_definitions:
            item = getattr(exceptions, item_name)
            text += get_class_reference(item, item_ast)

    with open("exceptions-reference.md", "w+") as fp:
        fp.write(text.strip())


def get_all_ast_definitions(all_names, root_module):
    names_set = set(all_names)
    checked_modules = []
    definitions = {}

    def visit_node(ast_node):
        if isinstance(ast_node, ast.Module):
            for i, node in enumerate(ast_node.body):
                visit_node(node)

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
                module = import_module(f"ariadne.{ast_node.module}")
                with open(module.__file__, "r") as fp:
                    module_ast = ast.parse(fp.read())
                    visit_node(module_ast)

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

    with open(root_module.__file__, "r") as fp:
        module_ast = ast.parse(fp.read())
        visit_node(module_ast)

    return definitions


def get_class_reference(obj, obj_ast: ast.ClassDef):
    reference = "```python\n"
    reference += f"class {obj_ast.name}"

    bases = [base.id for base in obj_ast.bases]
    if bases:
        reference += "(%s)" % (", ".join(bases))

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


def get_function_reference(obj, obj_ast: ast.AsyncFunctionDef | ast.FunctionDef):
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


def get_function_signature(obj_ast):
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


def parse_docstring(doc: str | None, depth: int = 0) -> ParsedDoc:
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

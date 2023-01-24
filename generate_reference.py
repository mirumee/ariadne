"""Introspect public API and generate reference from it."""
import ast
import inspect
from importlib import import_module
from textwrap import dedent, indent

import ariadne


def main():
    generate_api_reference()


def generate_api_reference():
    old_reference = get_previous_api_reference()

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

    items_docs = []

    all_names = sorted(ariadne.__all__)
    ast_definitions = get_all_ast_definitions(ariadne)

    for item_name in all_names:
        item_doc = f"## `{item_name}`"
        item_doc += "\n\n"
        
        if item_name in ast_definitions:
            item_ast = ast_definitions[item_name]
            if isinstance(item_ast, ast.ClassDef):
                item_doc += get_object_reference(old_reference.get(item_name), item_ast)
            if isinstance(item_ast, (ast.AsyncFunctionDef, ast.FunctionDef)):
                item_doc += get_function_reference(old_reference.get(item_name), item_ast)

            items_docs.append(item_doc)

    text += "\n\n\n"
    text += "\n\n\n- - - - -\n\n\n".join(items_docs)

    with open("api-reference.md", "w+") as fp:
        fp.write(text.strip())


def get_previous_api_reference():
    reference = ""
    with open("api-reference.md", "r") as fp:
        reference = fp.read().strip()

    reference = "\n" + reference[reference.index("##"):].strip()
    items = {}

    for section in reference.split("\n## "):
        section = section.strip().rstrip("- \n")
        if not section:
            continue

        obj_name = section[:section.index("\n")].strip("`")
        section = section[section.index("\n"):].strip()

        section = section[section.index("```python") + 9:].strip()
        section = section[section.index("```") + 3:].strip()

        if "\n#" in section:
            root = section[:section.index("\n#")].strip()
            section[section.index("\n#"):].strip()
        else:
            root = section.strip()

        data = {
            "_root": root,
        }

        if obj_name == "graphql":
            print(section)
            print()
            print(data)

        items[obj_name] = data

    return items


def get_all_ast_definitions(root_module):
    all_names = set(root_module.__all__)
    definitions = {}

    def visit_node(ast_node):
        if isinstance(ast_node, ast.Module):
            for node in ast_node.body:
                visit_node(node)

        elif isinstance(ast_node, ast.ImportFrom) and ast_node.level:
            imported_names = set([alias.name for alias in ast_node.names])
            if all_names.intersection(imported_names):
                module = import_module(f"ariadne.{ast_node.module}")
                with open(module.__file__, "r") as fp:
                    module_ast = ast.parse(fp.read())
                    visit_node(module_ast)

        elif isinstance(ast_node, (ast.AsyncFunctionDef, ast.FunctionDef, ast.ClassDef)):
            if ast_node.name in all_names:
                if ast_node.name not in definitions:
                    definitions[ast_node.name] = ast_node

        elif isinstance(ast_node, ast.Assign):
            name = ast_node.targets[0].id
            if name in all_names and name not in definitions:
                definitions[name] = ast_node


    with open(ariadne.__file__, "r") as fp:
        module_ast = ast.parse(fp.read())
        visit_node(module_ast)

    return definitions


def get_object_reference(old_reference, obj_ast: ast.ClassDef):
    reference = "```python\n"
    reference += f"class {obj_ast.name}"

    bases = [base.id for base in obj_ast.bases if base.id != "ObjectType"]
    if bases:
        reference += "(%s)" % (", ".join(bases))
    
    reference += ":\n"

    items = []
    for node in obj_ast.body:
        if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
            if node.name.startswith("_") and not node.name.startswith("__"):
                continue

            method = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
            method += f"def {node.name}"
            method += get_function_signature(node)
            method += ":"
            method += "\n    ..."
            items.append(method)

    reference += indent("\n\n".join(items), "    ")
    reference += "\n```\n\n"

    if old_reference and old_reference.get("_root"):
        reference += old_reference["_root"]
    else:
        reference += ">>>>FILL ME>>>>"

    return reference


def get_function_reference(old_reference, obj_ast: ast.AsyncFunctionDef | ast.FunctionDef):
    reference = "```python\n"

    if isinstance(obj_ast,  ast.AsyncFunctionDef):
        reference += "async "
    
    reference += f"def {obj_ast.name}"
    reference += get_function_signature(obj_ast)
    reference += ":\n"
    reference += "    ..."

    reference += "\n```\n\n"

    if old_reference and old_reference.get("_root"):
        reference += old_reference["_root"]
    else:
        reference += ">>>>FILL ME>>>>"

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

    signature_str += ") -> "
    signature_str += returns

    return signature_str


if __name__ == "__main__":
    main()

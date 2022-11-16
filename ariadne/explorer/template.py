"""Tiny templating engine for explorers HTML.

Supports:

{{ varname }} - renders html.escaped varname from template vars
{% if var1 ... %}content{% endif %} - renders block contents if all args are true
{% ifnot var1 ... %}content{% endif %} - renders block contents if all args aren't true
{% else %} - used inside if/ifnot blocks to render alternative contents
{% json varname %} - renders json string with varname contents
"""

import html
from enum import IntEnum
from os import path
from typing import List, Optional, Tuple


TEMPLATE_DIR = path.join(path.dirname(path.abspath(__file__)), "templates")


def read_template(template: str) -> str:
    template_path = path.join(TEMPLATE_DIR, template)
    with open(template_path, "r", encoding="utf-8") as fp:
        return fp.read()


class Token(IntEnum):
    STR = 0
    VAR = 1
    RAW = 2
    IF = 3
    IF_NOT = 4
    ELSE = 5
    ENDIF = 6


TokenBlock = Tuple[Token, Optional[str]]


def render_template(template: str, template_vars: Optional[dict] = None) -> str:
    document = parse_template(template)
    return document.render(template_vars or {})


def parse_template(template: str):
    tokens = tokenize_template(template)
    return build_template_ast(tokens)


def tokenize_template(template: str) -> List[TokenBlock]:
    tokens: List[TokenBlock] = []
    cursor = 0
    limit = len(template)

    while cursor <= limit:
        tokens_positions = [
            pos
            for pos in [template.find("{{", cursor), template.find("{%", cursor)]
            if pos >= 0
        ]
        if tokens_positions:
            new_cursor = min(tokens_positions)
            if new_cursor > cursor:
                tokens.append((Token.STR, template[cursor:new_cursor]))
                cursor = new_cursor
        else:
            # Eject from tokenizer by appending rest of template as string
            tokens.append((Token.STR, template[cursor:limit]))
            break

        if template[cursor : cursor + 2] == "{{":
            token, cursor = tokenize_var(template, cursor)
            tokens.append(token)
        elif template[cursor : cursor + 2] == "{%":
            token, cursor = tokenize_block(template, cursor)
            tokens.append(token)

    return tokens


def tokenize_var(template: str, cursor: int) -> Tuple[TokenBlock, int]:
    end = template.find("}}", cursor)
    if end == -1:
        raise ValueError(
            f"Unclosed variable tag at {cursor}: '{template[cursor:cursor+20]}...'"
        )

    var_name = template[cursor + 2 : end].strip()
    if not var_name:
        raise ValueError(
            f"Empty variable tag at {cursor}: '{template[cursor:cursor+20]}...'"
        )

    return (Token.VAR, var_name), end + 2


def tokenize_block(template: str, cursor: int) -> Tuple[TokenBlock, int]:
    token: TokenBlock

    end = template.find("%}", cursor)
    if end == -1:
        raise ValueError(
            f"Unclosed block tag at {cursor}: '{template[cursor:cursor+20]}...'"
        )

    block_content = template[cursor + 2 : end].strip()
    if not block_content:
        raise ValueError(
            f"Empty block tag at {cursor}: '{template[cursor:cursor+20]}...'"
        )

    block_words = [word.strip() for word in block_content.split(" ")]
    block_type, block_args = block_words[0], block_words[1:]
    args = " ".join(block_args)

    if block_type.lower() == "if":
        token = (Token.IF, args)
        if not args:
            raise ValueError(
                f"'if' block without arguments at {cursor}: "
                f"'{template[cursor:cursor+20]}...'"
            )

    elif block_type.lower() == "ifnot":
        token = (Token.IF_NOT, args)
        if not args:
            raise ValueError(
                f"'ifnot' block without arguments at {cursor}: "
                f"'{template[cursor:cursor+20]}...'"
            )

    elif block_type.lower() == "else":
        token = (Token.ELSE, None)
        if args:
            raise ValueError(
                f"'else' block with arguments at {cursor}: "
                f"'{template[cursor:cursor+20]}...'"
            )

    elif block_type.lower() == "endif":
        token = (Token.ENDIF, None)
        if args:
            raise ValueError(
                f"'endif' block with arguments at {cursor}: "
                f"'{template[cursor:cursor+20]}...'"
            )

    elif block_type.lower() == "raw":
        token = (Token.RAW, args)
        if not args:
            raise ValueError(
                f"'raw' block without arguments at {cursor}: "
                f"'{template[cursor:cursor+20]}...'"
            )

    else:
        raise ValueError(
            f"Unknown block at {cursor}: '{template[cursor:cursor+20]}...'"
        )

    return token, end + 2


def build_template_ast(tokens: List[TokenBlock]) -> "TemplateDocument":
    nodes = ast_to_nodes(tokens)
    return TemplateDocument(nodes)


def ast_to_nodes(tokens: List[TokenBlock]) -> List["TemplateNode"]:
    nodes: List[TemplateNode] = []
    i = 0
    limit = len(tokens)
    while i < limit:
        token_type, token_args = tokens[i]
        if token_type == Token.STR and token_args:
            nodes.append(TemplateText(token_args))
            i += 1
            continue

        if token_type == Token.VAR and token_args:
            nodes.append(TemplateVariable(token_args))
            i += 1
            continue

        if token_type == Token.RAW and token_args:
            nodes.append(TemplateVariable(token_args, escape=False))
            i += 1
            continue

        if token_type in (Token.IF, Token.IF_NOT) and token_args:
            if i + 1 == limit:
                raise ValueError("Unclosed 'if' block found.")

            if_block_args = token_args.split(" ")
            nesting = 0
            children: List[TokenBlock] = []
            if_not = token_type == Token.IF_NOT
            has_else = False
            for child in tokens[i + 1 :]:
                i += 1
                child_type = child[0]

                if child_type == Token.ENDIF:
                    if nesting == 0:
                        i += 1
                        break

                    nesting -= 1

                elif child_type == Token.ELSE:
                    if nesting == 0:
                        if has_else:
                            raise ValueError("Multiple 'else' clauses found.")

                        nodes.append(
                            TemplateIfBlock(
                                if_block_args,
                                ast_to_nodes(children),
                                if_not,
                            )
                        )
                        children = []
                        if_not = not if_not
                        has_else = True
                        continue

                elif child_type in (Token.IF, Token.IF_NOT):
                    nesting += 1

                children.append(child)
            else:
                raise ValueError("Unclosed 'if' block found.")

            nodes.append(
                TemplateIfBlock(
                    if_block_args,
                    ast_to_nodes(children),
                    if_not,
                )
            )
            continue

        if token_type == Token.ENDIF:
            raise ValueError("Extra 'endif' block found.")

    return nodes


class TemplateNode:
    def render(self, template_vars) -> str:
        raise NotImplementedError(
            "Subclasses of TemplateNode should define 'render' method."
        )


class TemplateDocument(TemplateNode):
    def __init__(self, nodes) -> None:
        self.nodes = nodes

    def render(self, template_vars) -> str:
        return "".join([node.render(template_vars) for node in self.nodes])


class TemplateText(TemplateNode):
    def __init__(self, value: str) -> None:
        self.value = value

    def render(self, _) -> str:
        return self.value


class TemplateIfBlock(TemplateNode):
    def __init__(self, args: List[str], nodes, if_not: bool = False) -> None:
        self.args = args
        self.nodes = nodes
        self.if_not = if_not

    def render(self, template_vars) -> str:
        args_true = all(template_vars.get(arg) for arg in self.args)
        block_true = not args_true if self.if_not else args_true
        if not block_true:
            return ""

        return "".join([node.render(template_vars) for node in self.nodes])


class TemplateVariable(TemplateNode):
    def __init__(self, var_name: str, escape: bool = True) -> None:
        self.var_name = var_name
        self.escape = escape

    def render(self, template_vars) -> str:
        if self.escape:
            return html.escape(str(template_vars.get(self.var_name) or ""))

        return str(template_vars.get(self.var_name) or "")

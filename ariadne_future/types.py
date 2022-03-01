from typing import Dict

from graphql import (
    DefinitionNode,
    FieldDefinitionNode,
    InputValueDefinitionNode,
)

FieldsDict = Dict[str, FieldDefinitionNode]
InputFieldsDict = Dict[str, InputValueDefinitionNode]
RequirementsDict = Dict[str, DefinitionNode]

from typing import Dict, Type

from graphql import (
    DefinitionNode,
    FieldDefinitionNode,
    InputValueDefinitionNode,
)

FieldsDict = Dict[str, FieldDefinitionNode]
InputFieldsDict = Dict[str, InputValueDefinitionNode]
RequirementsDict = Dict[str, Type[DefinitionNode]]

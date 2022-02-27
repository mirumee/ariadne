from typing import Dict

from graphql import (
    DefinitionNode,
    FieldDefinitionNode,
)

FieldsDict = Dict[str, FieldDefinitionNode]
RequirementsDict = Dict[str, DefinitionNode]

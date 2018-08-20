from typing import List, Union

from graphql.language.ast import Document

TypeDef = Union[str, Document]
TypeDefs = Union[TypeDef, List[TypeDef]]

from dataclasses import dataclass

from ariadne import InputType


@dataclass
class SomeInput:
    id: str
    message: str


dataclass_input = InputType("Name", lambda data: SomeInput(**data))

dict_input = InputType("Name", out_names={"fieldName": "field_name"})

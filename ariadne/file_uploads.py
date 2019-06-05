from typing import Optional, Union
from typing_extensions import Protocol

from .exceptions import HttpBadRequestError
from .scalars import ScalarType

SPEC_URL = "https://github.com/jaydenseric/graphql-multipart-request-spec"


class FilesDict(Protocol):
    def __getitem__(self, key):
        ...  # pragma: no-cover


def combine_multipart_data(
    operations: Union[dict, list], files_map: dict, files: FilesDict
) -> Union[dict, list]:
    if not isinstance(operations, (dict, list)):
        raise HttpBadRequestError(
            "Invalid type for the 'operations' multipart field ({}).".format(SPEC_URL)
        )
    if not isinstance(files_map, dict):
        raise HttpBadRequestError(
            "Invalid type for the 'map' multipart field ({}).".format(SPEC_URL)
        )

    files_map = inverse_files_map(files_map, files)
    if isinstance(operations, list):
        for i, operation in enumerate(operations):
            add_files_to_variables(
                operation.get("variables"), "{}.variables".format(i), files_map
            )
    if isinstance(operations, dict):
        add_files_to_variables(operations.get("variables"), "variables", files_map)
    return operations


def inverse_files_map(files_map: dict, files: FilesDict) -> dict:
    inverted_map = {}
    for field_name, paths in files_map.items():
        if not isinstance(paths, list):
            raise HttpBadRequestError(
                (
                    "Invalid type for the 'map' multipart field entry "
                    "key '{}' array ({})."
                ).format(field_name, SPEC_URL)
            )

        for i, path in enumerate(paths):
            if not isinstance(path, str):
                raise HttpBadRequestError(
                    (
                        "Invalid type for the 'map' multipart field entry key "
                        "'{}' array index '{}' value ({})."
                    ).format(field_name, i, SPEC_URL)
                )

            try:
                inverted_map[path] = files[field_name]
            except KeyError:
                raise HttpBadRequestError(
                    ("File data was missing for entry key '{}' ({}).").format(
                        field_name, SPEC_URL
                    )
                )

    return inverted_map


def add_files_to_variables(
    variables: Optional[Union[dict, list]], path: str, files_map: dict
):
    if isinstance(variables, dict):
        for variable, value in variables.items():
            variable_path = "{}.{}".format(path, variable)
            if isinstance(value, (dict, list)):
                add_files_to_variables(value, variable_path, files_map)
            elif value is None:
                variables[variable] = files_map.get(variable_path)

    if isinstance(variables, list):
        for i, value in enumerate(variables):
            variable_path = "{}.{}".format(path, i)
            if isinstance(value, (dict, list)):
                add_files_to_variables(value, variable_path, files_map)
            elif value is None:
                variables[i] = files_map.get(variable_path)


upload_scalar = ScalarType("Upload")


@upload_scalar.serializer
def serialize_upload(*_):
    raise ValueError("'Upload' scalar serialization is not supported.")


@upload_scalar.literal_parser
def parse_upload_literal(*_):
    raise ValueError("'Upload' scalar literal is not supported.")


@upload_scalar.value_parser
def parse_upload_value(value):
    return value

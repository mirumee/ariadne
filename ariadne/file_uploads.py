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
    """Populates `operations` variables with `files` using the `files_map`.

    Utility function for integration developers.

    Mutates `operations` in place, but also returns it.

    # Requires arguments

    `operations`: a `list` or `dict` with GraphQL operations to populate the file
    variables in. It contains `operationName`, `query` and `variables` keys, but
    implementation only cares about `variables` being present.

    `files_map`: a `dict` with mapping of `files` to `operations`. Keys correspond
    to keys in `files dict`, values are lists of strings with paths (eg.:
    `variables.key.0` maps to `operations["variables"]["key"]["0"]`).

    `files`: a `dict` of files. Keys are strings, values are environment specific
    representations of uploaded files.

    # Example

    Following example uses `combine_multipart_data` to populate the `image`
    variable with file object from `files`, using the `files_map` to know
    which variable to replace.

    ```python
    # Single GraphQL operation
    operations = {
        "operationName": "AvatarUpload",
        "query": \"\"\"
            mutation AvatarUpload($type: String!, $image: Upload!) {
                avatarUpload(type: $type, image: $image) {
                    success
                    errors
                }
            }
        \"\"\",
        "variables": {"type": "SQUARE", "image": None}
    }
    files_map = {"0": ["variables.image"]}
    files = {"0": UploadedFile(....)}

    combine_multipart_data(operations, files_map, files

    assert operations == {
        "variables": {"type": "SQUARE", "image": UploadedFile(....)}
    }
    ```
    """

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
            except KeyError as ex:
                raise HttpBadRequestError(
                    ("File data was missing for entry key '{}' ({}).").format(
                        field_name, SPEC_URL
                    )
                ) from ex

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


"""Optional Python logic for `Upload` scalar.

`Upload` scalar doesn't require any custom Python logic to work, but this utility 
sets `serializer` and `literal_parser` to raise ValueErrors when `Upload` is used 
either as return type for field or passed as literal value in GraphQL query.

# Example

Below code defines a schema with `Upload` scalar using `upload_scalar` utility:

```python
from ariadne import MutationType, make_executable_schema, upload_scalar

mutation_type = MutationType()

@mutation_type.field("handleUpload")
def resolve_handle_upload(*_, upload):
    return repr(upload)


schema = make_executable_schema(
    \"\"\"
    scalar Upload

    type Query {
        empty: String
    }

    type Mutation {
        handleUpload(upload: Upload!): String
    }
    \"\"\",
    upload_scalar,
    mutation_type,
)
```
"""
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

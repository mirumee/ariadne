from .exceptions import HttpBadRequestError

SPEC_URL = "https://github.com/jaydenseric/graphql-multipart-request-spec"


def set_files_in_operations(operations, files_map, files):
    files_map = inverse_files_map(files_map, files)
    if not files_map:
        return operations
    if isinstance(operations, list):
        for i, operation in enumerate(operations):
            add_files_to_variables(
                operation["variables"], "{}.variables".format(i), files_map
            )
    if isinstance(operations, dict):
        add_files_to_variables(operations["variables"], "variables", files_map)
    return operations


def inverse_files_map(files_map, files):
    inverted_map = {}
    for field_name, paths in files_map.items():
        if not isinstance(paths, list):
            raise HttpBadRequestError(
                f"Invalid type for the 'map' multipart field entry key '{field_name}' "
                f"array ({SPEC_URL})."
            )

        for i, path in enumerate(paths):
            if not isinstance(path, str):
                raise HttpBadRequestError(
                    f"Invalid type for the 'map' multipart field entry key "
                    f"'{field_name}' array index '{i}' value ({SPEC_URL})."
                )

            inverted_map[path] = files.get(field_name)

    return inverted_map


def add_files_to_variables(variables, path, files_map):
    if isinstance(variables, dict):
        for variable, value in variables.items():
            variable_path = "{}.{}".format(path, variable)
            if isinstance(value, list):
                add_files_to_variables(value, variable_path, files_map)
            elif isinstance(value, dict):
                add_files_to_variables(value, variable_path, files_map)
            elif value is None:
                variables[variable] = files_map.get(variable_path)

    if isinstance(variables, list):
        for i, value in enumerate(variables):
            variable_path = "{}.{}".format(path, i)
            if isinstance(value, list):
                add_files_to_variables(value, variable_path, files_map)
            elif isinstance(value, dict):
                add_files_to_variables(value, variable_path, files_map)
            elif value is None:
                variables[i] = files_map.get(variable_path)

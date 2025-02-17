import pytest

from ariadne.exceptions import HttpBadRequestError
from ariadne.file_uploads import combine_multipart_data, upload_scalar


def test_file_is_set_in_variable():
    operations = {"variables": {"file": None}}
    files_map = {"0": ["variables.file"]}
    files = {"0": True}

    assert combine_multipart_data(operations, files_map, files) == {
        "variables": {"file": True}
    }


def test_files_are_set_in_multiple_variables():
    operations = {"variables": {"fileA": None, "fileB": None}}
    files_map = {"0": ["variables.fileA"], "1": ["variables.fileB"]}
    files = {"0": "A", "1": "B"}

    assert combine_multipart_data(operations, files_map, files) == {
        "variables": {"fileA": "A", "fileB": "B"}
    }


def test_single_file_is_set_in_multiple_variables():
    operations = {"variables": {"fileA": None, "fileB": None}}
    files_map = {"0": ["variables.fileA", "variables.fileB"]}
    files = {"0": True}

    assert combine_multipart_data(operations, files_map, files) == {
        "variables": {"fileA": True, "fileB": True}
    }


def test_file_is_set_in_list_variable():
    operations = {"variables": {"files": [None]}}
    files_map = {"0": ["variables.files.0"]}
    files = {"0": True}

    assert combine_multipart_data(operations, files_map, files) == {
        "variables": {"files": [True]}
    }


def test_files_are_set_in_list_variable():
    operations = {"variables": {"files": [None, None]}}
    files_map = {"0": ["variables.files.0"], "1": ["variables.files.1"]}
    files = {"0": "A", "1": "B"}

    assert combine_multipart_data(operations, files_map, files) == {
        "variables": {"files": ["A", "B"]}
    }


def test_file_is_set_in_input_variable():
    operations = {"variables": {"input": {"file": None}}}
    files_map = {"0": ["variables.input.file"]}
    files = {"0": True}

    assert combine_multipart_data(operations, files_map, files) == {
        "variables": {"input": {"file": True}}
    }


def test_files_are_set_in_input_list_variable():
    operations = {"variables": {"input": {"files": [None, None]}}}
    files_map = {"0": ["variables.input.files.0"], "1": ["variables.input.files.1"]}
    files = {"0": "A", "1": "B"}

    assert combine_multipart_data(operations, files_map, files) == {
        "variables": {"input": {"files": ["A", "B"]}}
    }


def test_files_are_set_in_list_of_inputs_variable():
    operations = {"variables": {"input": [{"file": None}, {"file": None}]}}
    files_map = {"0": ["variables.input.0.file"], "1": ["variables.input.1.file"]}
    files = {"0": "A", "1": "B"}

    assert combine_multipart_data(operations, files_map, files) == {
        "variables": {"input": [{"file": "A"}, {"file": "B"}]}
    }


def test_file_is_set_in_one_operation_variable():
    operations = [{}, {"variables": {"file": None, "name": "test"}}]
    files_map = {"0": ["1.variables.file"]}
    files = {"0": True}

    assert combine_multipart_data(operations, files_map, files) == [
        {},
        {"variables": {"file": True, "name": "test"}},
    ]


def test_setting_file_value_in_variables_leaves_other_variables_unchanged():
    operations = {"variables": {"file": None, "name": "test"}}
    files_map = {"0": ["variables.file"]}
    files = {"0": True}

    assert combine_multipart_data(operations, files_map, files) == {
        "variables": {"file": True, "name": "test"}
    }


def test_error_is_raised_if_operations_value_is_not_a_list_or_dict():
    with pytest.raises(HttpBadRequestError):
        assert combine_multipart_data(None, {}, {})


def test_error_is_raised_if_map_value_is_not_a_list_or_dict():
    with pytest.raises(HttpBadRequestError):
        assert combine_multipart_data({}, None, {})


def test_error_is_raised_if_file_paths_value_is_not_a_list():
    operations = {"variables": {"file": None}}
    files_map = {"0": "variables.file"}
    files = {"0": True}

    with pytest.raises(HttpBadRequestError):
        assert combine_multipart_data(operations, files_map, files)


def test_error_is_raised_if_file_paths_list_item_is_not_a_str():
    operations = {"variables": {"file": None}}
    files_map = {"0": [1]}
    files = {"0": True}

    with pytest.raises(HttpBadRequestError):
        assert combine_multipart_data(operations, files_map, files)


def test_error_is_raised_if_file_described_in_map_is_not_found():
    operations = {"variables": {"file": None}}
    files_map = {"0": ["variables.file"]}
    files = {}

    with pytest.raises(HttpBadRequestError):
        assert combine_multipart_data(operations, files_map, files)


def test_default_upload_scalar_doesnt_support_serialization():
    with pytest.raises(ValueError):
        upload_scalar._serialize(True)


def test_default_upload_scalar_doesnt_support_literals():
    with pytest.raises(ValueError):
        upload_scalar._parse_literal(True)


def test_default_upload_scalar_passes_variable_value_as_is():
    assert upload_scalar._parse_value(True) is True

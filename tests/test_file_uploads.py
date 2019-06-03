from ariadne.exceptions import HttpBadRequestError
from ariadne.file_uploads import set_files_in_operations


def test_single_file_is_set_in_variable():
    operations = {"variables": {"file": None}}
    files_map = {"0": ["variables.file"]}
    files = {"0": True}

    assert set_files_in_operations(operations, files_map, files) == {
        "variables": {"file": True}
    }


def test_multiple_files_are_set_in_variables():
    operations = {"variables": {"fileA": None, "fileB": None}}
    files_map = {"0": ["variables.fileA"], "1": ["variables.fileB"]}
    files = {"0": "A", "1": "B"}

    assert set_files_in_operations(operations, files_map, files) == {
        "variables": {"fileA": "A", "fileB": "B"}
    }


def test_single_file_is_set_in_multiple_variables():
    operations = {"variables": {"fileA": None, "fileB": None}}
    files_map = {"0": ["variables.fileA", "variables.fileB"]}
    files = {"0": True}

    assert set_files_in_operations(operations, files_map, files) == {
        "variables": {"fileA": True, "fileB": True}
    }


def test_single_file_is_set_in_list_variable():
    operations = {"variables": {"files": [None]}}
    files_map = {"0": ["variables.files.0"]}
    files = {"0": True}

    assert set_files_in_operations(operations, files_map, files) == {
        "variables": {"files": [True]}
    }


def test_multiple_files_are_set_in_list_variable():
    operations = {"variables": {"files": [None, None]}}
    files_map = {"0": ["variables.files.0"], "1": ["variables.files.1"]}
    files = {"0": "A", "1": "B"}

    assert set_files_in_operations(operations, files_map, files) == {
        "variables": {"files": ["A", "B"]}
    }


def test_single_file_is_set_in_inputs_variable():
    operations = {"variables": {"input": {"file": None}}}
    files_map = {"0": ["variables.input.file"]}
    files = {"0": True}

    assert set_files_in_operations(operations, files_map, files) == {
        "variables": {"input": {"file": True}}
    }


def test_files_are_set_in_input_list_variable():
    operations = {"variables": {"input": {"files": [None, None]}}}
    files_map = {"0": ["variables.input.files.0"], "1": ["variables.input.files.1"]}
    files = {"0": "A", "1": "B"}

    assert set_files_in_operations(operations, files_map, files) == {
        "variables": {"input": {"files": ["A", "B"]}}
    }


def test_files_are_set_in_list_of_inputs_variable():
    operations = {"variables": {"input": [{"file": None}, {"file": None}]}}
    files_map = {"0": ["variables.input.0.file"], "1": ["variables.input.1.file"]}
    files = {"0": "A", "1": "B"}

    assert set_files_in_operations(operations, files_map, files) == {
        "variables": {"input": [{"file": "A"}, {"file": "B"}]}
    }

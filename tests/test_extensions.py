from unittest.mock import Mock

from ariadne import ExtensionManager
from ariadne.types import Extension


context = {}
exception = ValueError()
query = "{ test }"


def test_request_started_event_is_called_by_extension_manager():
    extension = Mock(spec=Extension)
    manager = ExtensionManager([Mock(return_value=extension)])
    with manager.request(context):
        pass

    extension.request_started.assert_called_once_with(context)


def test_request_finished_event_is_called_by_extension_manager():
    extension = Mock(spec=Extension)
    manager = ExtensionManager([Mock(return_value=extension)])
    with manager.request(context):
        pass

    extension.request_finished.assert_called_once_with(context)


def test_request_finished_event_is_called_with_error():
    extension = Mock(spec=Extension)
    manager = ExtensionManager([Mock(return_value=extension)])
    try:
        with manager.request(context):
            raise exception
    except:  # pylint: disable=bare-except
        pass

    extension.request_finished.assert_called_once_with(context, exception)


def test_parsing_started_event_is_called_by_extension_manager():
    extension = Mock(spec=Extension)
    manager = ExtensionManager([Mock(return_value=extension)])
    with manager.parsing(query):
        pass

    extension.parsing_started.assert_called_once_with(query)


def test_parsing_finished_event_is_called_by_extension_manager():
    extension = Mock(spec=Extension)
    manager = ExtensionManager([Mock(return_value=extension)])
    with manager.parsing(query):
        pass

    extension.parsing_finished.assert_called_once_with(query)


def test_parsing_finished_event_is_called_with_error():
    extension = Mock(spec=Extension)
    manager = ExtensionManager([Mock(return_value=extension)])
    try:
        with manager.parsing(query):
            raise exception
    except:  # pylint: disable=bare-except
        pass

    extension.parsing_finished.assert_called_once_with(query, exception)


def test_validation_started_event_is_called_by_extension_manager():
    extension = Mock(spec=Extension)
    manager = ExtensionManager([Mock(return_value=extension)])
    with manager.validation(context):
        pass

    extension.validation_started.assert_called_once_with(context)


def test_validation_finished_event_is_called_by_extension_manager():
    extension = Mock(spec=Extension)
    manager = ExtensionManager([Mock(return_value=extension)])
    with manager.validation(context):
        pass

    extension.validation_finished.assert_called_once_with(context)


def test_validation_finished_event_is_called_with_error():
    extension = Mock(spec=Extension)
    manager = ExtensionManager([Mock(return_value=extension)])
    try:
        with manager.validation(context):
            raise exception
    except:  # pylint: disable=bare-except
        pass

    extension.validation_finished.assert_called_once_with(context, exception)


def test_execution_started_event_is_called_by_extension_manager():
    extension = Mock(spec=Extension)
    manager = ExtensionManager([Mock(return_value=extension)])
    with manager.execution(context):
        pass

    extension.execution_started.assert_called_once_with(context)


def test_execution_finished_event_is_called_by_extension_manager():
    extension = Mock(spec=Extension)
    manager = ExtensionManager([Mock(return_value=extension)])
    with manager.execution(context):
        pass

    extension.execution_finished.assert_called_once_with(context)


def test_execution_finished_event_is_called_with_error():
    extension = Mock(spec=Extension)
    manager = ExtensionManager([Mock(return_value=extension)])
    try:
        with manager.execution(context):
            raise exception
    except:  # pylint: disable=bare-except
        pass

    extension.execution_finished.assert_called_once_with(context, exception)


def test_has_errors_event_is_called_with_errors_list():
    extension = Mock(spec=Extension)
    manager = ExtensionManager([Mock(return_value=extension)])
    manager.has_errors([exception])
    extension.has_errors.assert_called_once_with([exception])


def test_extensions_are_formatted():
    extensions = [
        Mock(spec=Extension, format=Mock(return_value={"a": 1})),
        Mock(spec=Extension, format=Mock(return_value={"b": 2})),
    ]
    manager = ExtensionManager([Mock(return_value=ext) for ext in extensions])
    assert manager.format() == {"a": 1, "b": 2}

from unittest.mock import MagicMock

from ariadne.middleware import convert_kwargs_to_snake_case_middleware


def test_kwargs_converted_to_snake_case():
    resolver, parent, info = MagicMock(), None, MagicMock()
    kwargs = {"convertThisPlease": None}
    convert_kwargs_to_snake_case_middleware(resolver, parent, info, **kwargs)
    resolver.assert_called_once_with(parent, info, convert_this_please=None)


def test_kwargs_not_converted_to_snake_case_if_introspection_query():
    resolver, parent, info = MagicMock(), None, MagicMock()
    info.path.as_list = MagicMock(return_value=["__schema"])
    kwargs = {"convertThisPlease": None}
    convert_kwargs_to_snake_case_middleware(resolver, parent, info, **kwargs)
    resolver.assert_called_once_with(parent, info, **kwargs)

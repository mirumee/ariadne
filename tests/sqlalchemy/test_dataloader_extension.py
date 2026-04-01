from unittest.mock import Mock

import pytest

from ariadne.contrib.sqlalchemy import LoaderRegistry, SQLAlchemyDataLoaderExtension


@pytest.fixture
def session():
    return Mock(name="session")


def test_request_started_creates_loader_registry(session):
    ext = SQLAlchemyDataLoaderExtension()
    context = {"session": session}

    ext.request_started(context)

    assert isinstance(context["loader_registry"], LoaderRegistry)
    assert context["loader_registry"].session is session

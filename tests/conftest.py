from unittest.mock import Mock

import pytest


@pytest.fixture
def first_name():
    return "Joe"


@pytest.fixture
def avatar():
    return "test-url.com"


@pytest.fixture
def blog_posts():
    return 3


@pytest.fixture
def mock_user(first_name, avatar, blog_posts):
    return Mock(
        first_name=Mock(return_value=first_name),
        avatar=Mock(return_value=avatar),
        blog_posts=Mock(return_value=blog_posts),
    )

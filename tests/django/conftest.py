import pytest
from django.conf import settings
from django.test import RequestFactory


def pytest_configure():
    settings.configure(
        USE_TZ=True,
        TIME_ZONE="America/Chicago",
        INSTALLED_APPS=["ariadne.contrib.django"],
        TEMPLATES=[
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "APP_DIRS": True,
            }
        ],
    )


@pytest.fixture
def request_factory():
    return RequestFactory()

import pytest
from django.conf import settings
from django.test import RequestFactory


def pytest_configure():
    settings.configure(
        USE_TZ=True,
        TIME_ZONE="America/Chicago",
        DATABASES={
            "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:",}
        },
        INSTALLED_APPS=("rest_framework", "ariadne.contrib.django", "tests.django",),
        TEMPLATES=[
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "APP_DIRS": True,
            }
        ],
    )

    import django  # pylint: disable=import-outside-toplevel

    django.setup()


@pytest.fixture
def request_factory():
    return RequestFactory()

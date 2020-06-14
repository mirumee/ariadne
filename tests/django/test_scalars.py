# pylint: disable=comparison-with-callable,protected-access
import pytest
from django.utils import timezone

from ariadne.contrib.django.scalars import (
    date_scalar,
    datetime_scalar,
    parse_date_value,
    parse_datetime_value,
    serialize_date,
    serialize_datetime,
)


@pytest.fixture
def datetime():
    return timezone.now()


@pytest.fixture
def date(datetime):
    return datetime.date()


def test_date_serializer_serializes_datetime(datetime, date):
    assert serialize_date(datetime) == date.isoformat()


def test_date_serializer_serializes_date(date):
    assert serialize_date(date) == date.isoformat()


def test_date_parser_returns_valid_date_from_datetime_iso8601_str(datetime, date):
    assert parse_date_value(datetime.isoformat()) == date


def test_date_parser_returns_valid_date_from_date_iso8601_str(date):
    assert parse_date_value(date.isoformat()) == date


def test_date_parser_returns_valid_date_from_other_date_str(date):
    assert parse_date_value(date.strftime("%m/%d/%Y")) == date


def test_date_parser_raises_value_error_on_invalid_data():
    with pytest.raises(ValueError):
        parse_date_value("nothing")


def test_datetime_serializer_serializes_datetime(datetime):
    assert serialize_datetime(datetime) == datetime.isoformat()


def test_datetime_serializer_serializes_date(datetime, date):
    assert serialize_datetime(date) == datetime.date().isoformat()


def test_datetime_parser_returns_valid_date_from_datetime_iso8601_str(datetime):
    assert parse_datetime_value(datetime.isoformat()) == datetime


def test_datetime_parser_returns_valid_date_from_date_iso8601_str(date):
    # time data is lost when datetime scalar receives date
    assert parse_datetime_value(date.isoformat()).date() == date


def test_datetime_parser_returns_valid_date_from_other_date_str(date):
    # time data is lost when datetime scalar receives date
    assert parse_datetime_value(date.strftime("%m/%d/%Y")).date() == date


def test_datetime_parser_raises_value_error_on_invalid_data():
    with pytest.raises(ValueError):
        parse_datetime_value("nothing")


def test_date_scalar_has_serializer_set():
    assert date_scalar._serialize == serialize_date


def test_date_scalar_has_value_parser_set():
    assert date_scalar._parse_value == parse_date_value


def test_datetime_scalar_has_serializer_set():
    assert datetime_scalar._serialize == serialize_datetime


def test_datetime_scalar_has_value_parser_set():
    assert datetime_scalar._parse_value == parse_datetime_value

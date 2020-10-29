# pylint: disable=comparison-with-callable,protected-access
import pytest
from django.utils import timezone

from ariadne.contrib.django.scalars import (
    date_scalar,
    datetime_scalar,
    parse_date_value,
    parse_datetime_value,
    parse_time_value,
    serialize_date,
    serialize_datetime,
    serialize_time,
    time_scalar,
)


@pytest.fixture
def datetime():
    return timezone.now()


@pytest.fixture
def date(datetime):
    return datetime.date()


@pytest.fixture
def time(datetime):
    return datetime.time()


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


def test_time_serializer_serializes_time(time):
    assert serialize_time(time) == time.isoformat()


def test_time_parser_returns_valid_time_from_datetime_iso8601_str(datetime, time):
    assert parse_time_value(datetime.isoformat()) == time


def test_time_parser_returns_valid_time_from_time_iso8601_str(time):
    assert parse_time_value(time.isoformat()) == time


def test_time_parser_returns_valid_time_from_other_time_str(time):
    assert parse_time_value(time.strftime("%H:%M:%S.%f")) == time


def test_time_parser_raises_value_error_on_invalid_data():
    with pytest.raises(ValueError):
        parse_time_value("nothing")


def test_date_scalar_has_serializer_set():
    assert date_scalar._serialize == serialize_date


def test_date_scalar_has_value_parser_set():
    assert date_scalar._parse_value == parse_date_value


def test_datetime_scalar_has_serializer_set():
    assert datetime_scalar._serialize == serialize_datetime


def test_datetime_scalar_has_value_parser_set():
    assert datetime_scalar._parse_value == parse_datetime_value


def test_time_scalar_has_serializer_set():
    assert time_scalar._serialize == serialize_time


def test_time_scalar_has_value_parser_set():
    assert time_scalar._parse_value == parse_time_value

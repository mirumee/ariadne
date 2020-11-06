# pylint: disable=comparison-with-callable,protected-access
import uuid
from decimal import Decimal, InvalidOperation

import pytest
from django.utils import timezone

from ariadne.contrib.django.scalars import (
    date_scalar,
    datetime_scalar,
    decimal_scalar,
    uuid_scalar,
    parse_date_value,
    parse_datetime_value,
    parse_decimal_value,
    parse_uuid_value,
    serialize_date,
    serialize_datetime,
    serialize_decimal,
    serialize_uuid,
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


def test_decimal_serializer_serializes_decimal():
    assert serialize_decimal(Decimal("5.0")) == "5.0"


def test_uuid_serializer_serializes_uuid():
    uuid_str = "e6cbf26a-327f-4fd6-9d28-25738a47e303"
    assert serialize_uuid(uuid.UUID(uuid_str)) == uuid_str


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


def test_decimal_parser_parses_string():
    assert parse_decimal_value("5.0") == Decimal("5.0")


def test_decimal_parser_parses_integer():
    assert parse_decimal_value(5) == Decimal("5")


def test_decimal_parser_raises_invalid_operation_on_invalid_data():
    with pytest.raises(InvalidOperation):
        parse_decimal_value("meow")


def test_uuid_parser_parses_uuid_string():
    uuid_str = "bb7efd70-b1cd-11ea-a5af-0242ac130006"
    assert parse_uuid_value(uuid_str) == uuid.UUID(uuid_str)


def test_uuid_parser_raises_value_error_on_invalid_data():
    with pytest.raises(ValueError):
        parse_uuid_value("nothing")


def test_date_scalar_has_serializer_set():
    assert date_scalar._serialize == serialize_date


def test_date_scalar_has_value_parser_set():
    assert date_scalar._parse_value == parse_date_value


def test_datetime_scalar_has_serializer_set():
    assert datetime_scalar._serialize == serialize_datetime


def test_datetime_scalar_has_value_parser_set():
    assert datetime_scalar._parse_value == parse_datetime_value


def test_decimal_scalar_has_serializer_set():
    assert decimal_scalar._serialize == serialize_decimal


def test_decimal_scalar_has_value_parser_set():
    assert decimal_scalar._parse_value == parse_decimal_value


def test_uuid_scalar_has_serializer_set():
    assert uuid_scalar._serialize == serialize_uuid


def test_uuid_scalar_has_value_parser_set():
    assert uuid_scalar._parse_value == parse_uuid_value

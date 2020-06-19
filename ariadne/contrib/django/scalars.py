from datetime import date, datetime
from decimal import Decimal
from typing import Any, List, Optional, Union
import uuid

import dateutil.parser
from django.forms.utils import from_current_timezone
from django.utils import formats
from django.utils.translation import gettext_lazy as _

from ...scalars import ScalarType


date_input_formats = formats.get_format_lazy("DATE_INPUT_FORMATS")
datetime_input_formats = formats.get_format_lazy("DATETIME_INPUT_FORMATS")

date_scalar = ScalarType("Date")
datetime_scalar = ScalarType("DateTime")
decimal_scalar = ScalarType("Decimal")
uuid_scalar = ScalarType("UUID")


@date_scalar.serializer
def serialize_date(value: Union[date, datetime]) -> str:
    if isinstance(value, datetime):
        value = value.date()
    return value.isoformat()


@date_scalar.value_parser
def parse_date_value(value: Any) -> date:
    parsed_value = parse_value(value, date_input_formats)
    if not parsed_value:
        raise ValueError(_("Enter a valid date."))
    return parsed_value.date()


@datetime_scalar.serializer
def serialize_datetime(value: datetime) -> str:
    return value.isoformat()


@datetime_scalar.value_parser
def parse_datetime_value(value: Any) -> datetime:
    parsed_value = parse_value(value, datetime_input_formats)
    if not parsed_value:
        raise ValueError(_("Enter a valid date/time."))
    return from_current_timezone(parsed_value)


@decimal_scalar.serializer
def serialize_decimal(value: Decimal) -> str:
    return formats.number_format(value)


@decimal_scalar.value_parser
def parse_decimal_value(value: Any) -> Decimal:
    return Decimal(formats.sanitize_separators(value))


@uuid_scalar.serializer
def serialize_uuid(value: uuid.UUID) -> str:
    return str(value)


@uuid_scalar.value_parser
def parse_uuid_value(value: str) -> uuid.UUID:
    return uuid.UUID(value)


def parse_value(value: Any, formats: List[str]) -> Optional[datetime]:
    for format_str in formats:
        try:
            return datetime.strptime(value, format_str)
        except (ValueError, TypeError):
            continue

    # fallback to using dateutil parser
    try:
        return dateutil.parser.parse(value)
    except (ValueError, TypeError):
        return None

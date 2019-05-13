from datetime import date, datetime
from typing import Any, List, Optional, Union

import dateutil.parser
from django.forms.utils import from_current_timezone
from django.utils import formats
from django.utils.translation import gettext_lazy as _

from ...scalars import ScalarType


date_input_formats = formats.get_format_lazy("DATE_INPUT_FORMATS")
datetime_input_formats = formats.get_format_lazy("DATETIME_INPUT_FORMATS")

date_scalar = ScalarType("Date")
datetime_scalar = ScalarType("DateTime")


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

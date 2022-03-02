# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import GenericRepr, Snapshot


snapshots = Snapshot()

snapshots['test_executable_schema_raises_value_error_if_merged_types_define_same_field 1'] = GenericRepr('<ExceptionInfo ValueError("Multiple Query types are defining same field \'city\': CityQueryType, YearQueryType") tblen=5>')

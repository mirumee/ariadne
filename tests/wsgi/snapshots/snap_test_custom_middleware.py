# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_custom_middleware_executes_query_with_custom_query_context 1"] = {
    "data": {"hasValidAuth": True}
}

snapshots["test_custom_middleware_executes_query_with_custom_query_root 1"] = {
    "data": {"user": True}
}

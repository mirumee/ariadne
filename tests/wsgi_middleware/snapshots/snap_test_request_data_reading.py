# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots[
    "test_attempt_parse_request_missing_content_type_raises_bad_request_error 1"
] = [b"Posted content must be of type application/json"]

snapshots["test_attempt_parse_non_json_request_raises_bad_request_error 1"] = [
    b"Posted content must be of type application/json"
]

snapshots[
    "test_attempt_get_content_length_from_missing_header_raises_bad_request_error 1"
] = [b"content length header is missing or incorrect"]

snapshots[
    "test_attempt_get_content_length_from_malformed_header_raises_bad_request_error 1"
] = [b"content length header is missing or incorrect"]

snapshots[
    "test_attempt_get_request_body_from_missing_wsgi_input_raises_bad_request_error 1"
] = [b"Request body cannot be empty"]

snapshots[
    "test_attempt_get_request_body_from_empty_wsgi_input_raises_bad_request_error 1"
] = [b"Request body cannot be empty"]

snapshots["test_attempt_parse_non_json_request_body_raises_bad_request_error 1"] = [
    b"Request body is not a valid JSON"
]

snapshots[
    "test_attempt_parse_json_scalar_request_raises_graphql_bad_request_error 1"
] = {"errors": [{"message": "Valid request body should be a JSON object"}]}

snapshots[
    "test_attempt_parse_json_array_request_raises_graphql_bad_request_error 1"
] = {"errors": [{"message": "Valid request body should be a JSON object"}]}

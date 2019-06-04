# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_attempt_parse_request_missing_content_type_raises_bad_request_error 1'] = 'Posted content must be of type application/json or multipart/form-data'

snapshots['test_attempt_parse_non_json_request_raises_bad_request_error 1'] = 'Posted content must be of type application/json or multipart/form-data'

snapshots['test_attempt_parse_non_json_request_body_raises_bad_request_error 1'] = 'Request body is not a valid JSON'

snapshots['test_attempt_parse_json_scalar_request_raises_graphql_bad_request_error 1'] = '{"errors":[{"message":"Operation data should be a JSON object","locations":null,"path":null}]}'

snapshots['test_attempt_parse_json_array_request_raises_graphql_bad_request_error 1'] = '{"errors":[{"message":"Operation data should be a JSON object","locations":null,"path":null}]}'

snapshots['test_multipart_form_request_fails_if_operations_is_not_valid_json 1'] = b"Request 'operations' multipart field is not a valid JSON"

snapshots['test_multipart_form_request_fails_if_map_is_not_valid_json 1'] = b"Request 'map' multipart field is not a valid JSON"

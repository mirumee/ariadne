# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_attempt_execute_complex_query_without_variables_returns_error_json 1'] = {
    'data': None,
    'errors': [
        {
            'locations': [
                {
                    'column': 18,
                    'line': 2
                }
            ],
            'message': "Variable '$name' of required type 'String!' was not provided."
        }
    ]
}

snapshots['test_attempt_execute_query_with_invalid_operation_name_string_returns_error_json 1'] = {
    'data': None,
    'errors': [
        {
            'message': "Unknown operation named 'otherOperation'."
        }
    ]
}

snapshots['test_attempt_execute_query_with_invalid_operation_name_type_returns_error_json 1'] = {
    'errors': [
        {
            'message': '"[1, 2, 3]" is not a valid operation name.'
        }
    ]
}

snapshots['test_attempt_execute_query_with_invalid_variables_returns_error_json 1'] = {
    'errors': [
        {
            'message': 'Query variables must be a null or an object.'
        }
    ]
}

snapshots['test_attempt_execute_query_with_non_string_query_returns_error_json 1'] = {
    'errors': [
        {
            'message': 'The query must be a string.'
        }
    ]
}

snapshots['test_attempt_execute_query_without_query_entry_returns_error_json 1'] = {
    'errors': [
        {
            'message': 'The query must be a string.'
        }
    ]
}

snapshots['test_complex_query_is_executed_for_post_json_request 1'] = {
    'data': {
        'hello': 'Hello, Bob!'
    }
}

snapshots['test_complex_query_without_operation_name_executes_successfully 1'] = {
    'data': {
        'hello': 'Hello, Bob!'
    }
}

snapshots['test_query_is_executed_for_multipart_form_request_with_file 1'] = [
    b'{"data": {"upload": "FieldStorage"}}'
]

snapshots['test_query_is_executed_for_post_json_request 1'] = {
    'data': {
        'status': True
    }
}

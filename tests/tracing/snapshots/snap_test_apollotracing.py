# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_apollotracing_extension_adds_tracing_data_to_async_result_extensions 1'] = {
    'data': {
        'status': True
    },
    'extensions': {
        'tracing': {
            'duration': 0,
            'endTime': '2012-01-14T03:21:34.000000Z',
            'execution': {
                'resolvers': [
                    {
                        'duration': 0,
                        'fieldName': 'status',
                        'parentType': 'Query',
                        'path': [
                            'status'
                        ],
                        'returnType': 'Boolean',
                        'startOffset': 0
                    }
                ]
            },
            'startTime': '2012-01-14T03:21:34.000000Z',
            'version': 1
        }
    }
}

snapshots['test_apollotracing_extension_adds_tracing_data_to_sync_result_extensions 1'] = {
    'data': {
        'status': True
    },
    'extensions': {
        'tracing': {
            'duration': 0,
            'endTime': '2012-01-14T03:21:34.000000Z',
            'execution': {
                'resolvers': [
                    {
                        'duration': 0,
                        'fieldName': 'status',
                        'parentType': 'Query',
                        'path': [
                            'status'
                        ],
                        'returnType': 'Boolean',
                        'startOffset': 0
                    }
                ]
            },
            'startTime': '2012-01-14T03:21:34.000000Z',
            'version': 1
        }
    }
}

snapshots['test_apollotracing_extension_handles_exceptions_in_resolvers_in_async_context 1'] = {
    'testError': None
}

snapshots['test_apollotracing_extension_handles_exceptions_in_resolvers_in_sync_context 1'] = {
    'testError': None
}

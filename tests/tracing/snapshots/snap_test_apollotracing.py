# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_apollotracing_extension_adds_tracing_data_to_result_extensions 1'] = {
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

snapshots['test_apollotracing_extension_handles_exceptions_in_resolvers 1'] = {
    'data': {
        'testError': None
    },
    'errors': [
        {
            'locations': [
                (
                    1,
                    3
                )
            ],
            'message': 'Test exception',
            'path': [
                'testError'
            ]
        }
    ],
    'extensions': {
        'tracing': {
            'duration': 0,
            'endTime': '2012-01-14T03:21:34.000000Z',
            'execution': {
                'resolvers': [
                    {
                        'duration': 0,
                        'fieldName': 'testError',
                        'parentType': 'Query',
                        'path': [
                            'testError'
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

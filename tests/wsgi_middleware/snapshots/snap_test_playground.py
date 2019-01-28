# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_playground_html_is_served_on_get_request 1"] = [
    b'<!DOCTYPE html>\n<html>\n\n<head>\n  <meta charset=utf-8/>\n  <meta name="viewport" content="user-scalable=no, initial-scale=1.0, minimum-scale=1.0, maximum-scale=1.0, minimal-ui">\n  <title>GraphQL Playground</title>\n  <link rel="stylesheet" href="//cdn.jsdelivr.net/npm/graphql-playground-react/build/static/css/index.css" />\n  <link rel="shortcut icon" href="//cdn.jsdelivr.net/npm/graphql-playground-react/build/favicon.png" />\n  <script src="//cdn.jsdelivr.net/npm/graphql-playground-react/build/static/js/middleware.js"></script>\n</head>\n\n<body>\n  <div id="root">\n    <style>\n      body {\n        background-color: rgb(23, 42, 58);\n        font-family: Open Sans, sans-serif;\n        height: 90vh;\n      }\n      #root {\n        height: 100%;\n        width: 100%;\n        display: flex;\n        align-items: center;\n        justify-content: center;\n      }\n      .loading {\n        font-size: 32px;\n        font-weight: 200;\n        color: rgba(255, 255, 255, .6);\n        margin-left: 20px;\n      }\n      img {\n        width: 78px;\n        height: 78px;\n      }\n      .title {\n        font-weight: 400;\n      }\n    </style>\n    <img src=\'//cdn.jsdelivr.net/npm/graphql-playground-react/build/logo.png\' alt=\'\'>\n    <div class="loading"> Loading\n      <span class="title">GraphQL Playground</span>\n    </div>\n  </div>\n  <script>window.addEventListener(\'load\', function (event) {\n      GraphQLPlayground.init(document.getElementById(\'root\'), {\n        // options as \'endpoint\' belong here\n      })\n    })</script>\n</body>\n\n</html>'
]

# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_405_bad_method_is_served_on_get_request_for_disabled_explorer 1'] = []

snapshots['test_default_explorer_html_is_served_on_get_request 1'] = [b'''<!--
 *  Copyright (c) 2021 GraphQL Contributors
 *  All rights reserved.
 *
 *  This source code is licensed under the license found in the
 *  LICENSE file in the root directory of this source tree.
-->
<!DOCTYPE html>
<html>
  <head>
    <title>Ariadne GraphQL</title>
    <style>
      body {
        height: 100%;
        margin: 0;
        width: 100%;
        overflow: hidden;
      }

      #graphiql {
        height: 100vh;
      }
    </style>

    <link rel="stylesheet" href="https://unpkg.com/graphiql/graphiql.min.css" />
  </head>

  <body>
    <div id="graphiql">Loading...</div>

    <script
      crossorigin
      src="https://unpkg.com/react@17/umd/react.development.js"
    ></script>
    <script
      crossorigin
      src="https://unpkg.com/react-dom@17/umd/react-dom.development.js"
    ></script>

    <script
      crossorigin
      src="https://unpkg.com/graphiql/graphiql.min.js"
    ></script>


    <script>
      var fetcher = GraphiQL.createFetcher({
        url: window.location.href,
      });

      function GraphiQLWithExplorer() {
        var [query, setQuery] = React.useState(
          '#\n# GraphiQL is an in -browser tool for writing, validating, and\n# testing GraphQL queries.\n#\n# Type queries into this side of the screen, and you will see intelligent\n# typeaheads aware of the current GraphQL type schema and live syntax and\n# validation errors highlighted within the text.\n#\n# GraphQL queries typically start with a "{" character. Lines that start\n# with a # are ignored.\n#\n# An example GraphQL query might look like:\n#\n#     {\n#       field(arg: "value") {\n#         subField\n#\n#       }\n#\n#     }\n#\n# Keyboard shortcuts:\n#\n#   Prettify query: Shift - Ctrl - P(or press the prettify button)\n#\n#  Merge fragments: Shift - Ctrl - M(or press the merge button)\n#\n#        Run Query: Ctrl - Enter(or press the play button)\n#\n#    Auto Complete: Ctrl - Space(or just start typing)\n#',
        );
        return React.createElement(GraphiQL, {
          fetcher: fetcher,
          defaultEditorToolsVisibility: true,
          query: query,
          onEditQuery: setQuery,
        });
      }

      ReactDOM.render(
        React.createElement(GraphiQLWithExplorer),
        document.getElementById('graphiql'),
      );
    </script>
  </body>
</html>
''']

snapshots['test_graphiql_html_is_served_on_get_request 1'] = [b'''<!--
 *  Copyright (c) 2021 GraphQL Contributors
 *  All rights reserved.
 *
 *  This source code is licensed under the license found in the
 *  LICENSE file in the root directory of this source tree.
-->
<!DOCTYPE html>
<html>
  <head>
    <title>Ariadne GraphQL</title>
    <style>
      body {
        height: 100%;
        margin: 0;
        width: 100%;
        overflow: hidden;
      }

      #graphiql {
        height: 100vh;
      }
    </style>

    <link rel="stylesheet" href="https://unpkg.com/graphiql/graphiql.min.css" />
  </head>

  <body>
    <div id="graphiql">Loading...</div>

    <script
      crossorigin
      src="https://unpkg.com/react@17/umd/react.development.js"
    ></script>
    <script
      crossorigin
      src="https://unpkg.com/react-dom@17/umd/react-dom.development.js"
    ></script>

    <script
      crossorigin
      src="https://unpkg.com/graphiql/graphiql.min.js"
    ></script>


    <script>
      var fetcher = GraphiQL.createFetcher({
        url: window.location.href,
      });

      function GraphiQLWithExplorer() {
        var [query, setQuery] = React.useState(
          '#\n# GraphiQL is an in -browser tool for writing, validating, and\n# testing GraphQL queries.\n#\n# Type queries into this side of the screen, and you will see intelligent\n# typeaheads aware of the current GraphQL type schema and live syntax and\n# validation errors highlighted within the text.\n#\n# GraphQL queries typically start with a "{" character. Lines that start\n# with a # are ignored.\n#\n# An example GraphQL query might look like:\n#\n#     {\n#       field(arg: "value") {\n#         subField\n#\n#       }\n#\n#     }\n#\n# Keyboard shortcuts:\n#\n#   Prettify query: Shift - Ctrl - P(or press the prettify button)\n#\n#  Merge fragments: Shift - Ctrl - M(or press the merge button)\n#\n#        Run Query: Ctrl - Enter(or press the play button)\n#\n#    Auto Complete: Ctrl - Space(or just start typing)\n#',
        );
        return React.createElement(GraphiQL, {
          fetcher: fetcher,
          defaultEditorToolsVisibility: true,
          query: query,
          onEditQuery: setQuery,
        });
      }

      ReactDOM.render(
        React.createElement(GraphiQLWithExplorer),
        document.getElementById('graphiql'),
      );
    </script>
  </body>
</html>
''']

snapshots['test_apollo_html_is_served_on_get_request 1'] = [b'''<title>Ariadne GraphQL</title>
<div style="width: 100%; height: 100%;" id='embedded-sandbox'></div>
<script src="https://embeddable-sandbox.cdn.apollographql.com/_latest/embeddable-sandbox.umd.production.min.js"></script> 
<script>
  new window.EmbeddedSandbox({
    target: '#embedded-sandbox',
    initialEndpoint: window.location.href,
    initialState: {
      document: '# Write your query or mutation here',
      variables: {},
      headers: {},
    },
    includeCookies: false,
  });
</script>
''']

snapshots['test_playground_html_is_served_on_get_request 1'] = [
    b'<!DOCTYPE html>\n<html>\n\n<head>\n  <meta charset="utf-8" />\n  <meta name="viewport" content="user-scalable=no, initial-scale=1.0, minimum-scale=1.0, maximum-scale=1.0, minimal-ui">\n  <title>Ariadne GraphQL</title>\n  <link rel="stylesheet" href="//cdn.jsdelivr.net/npm/graphql-playground-react/build/static/css/index.css" />\n  <link rel="shortcut icon" href="//cdn.jsdelivr.net/npm/graphql-playground-react/build/favicon.png" />\n  <script src="//cdn.jsdelivr.net/npm/graphql-playground-react/build/static/js/middleware.js"></script>\n</head>\n\n<body>\n  <div id="root">\n    <style>\n      body {\n        background-color: rgb(23, 42, 58);\n        font-family: Open Sans, sans-serif;\n        height: 90vh;\n      }\n\n      #root {\n        height: 100%;\n        width: 100%;\n        display: flex;\n        align-items: center;\n        justify-content: center;\n      }\n\n      .loading {\n        font-size: 32px;\n        font-weight: 200;\n        color: rgba(255, 255, 255, .6);\n        margin-left: 20px;\n      }\n\n      img {\n        width: 78px;\n        height: 78px;\n      }\n\n      .title {\n        font-weight: 400;\n      }\n    </style>\n    <img src=\'//cdn.jsdelivr.net/npm/graphql-playground-react/build/logo.png\' alt=\'\'>\n    <div class="loading"> Loading\n      <span class="title">Ariadne GraphQL</span>\n    </div>\n  </div>\n  <script>window.addEventListener(\'load\', function (event) {\n      GraphQLPlayground.init(document.getElementById(\'root\'), {\n        // options as \'endpoint\' belong here\n        \n      })\n    })</script>\n</body>\n</html>\n'
]

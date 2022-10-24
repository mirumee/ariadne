# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_405_bad_method_is_served_on_get_request_for_disabled_explorer 1'] = ''

snapshots['test_apollo_html_is_served_on_get_request 1'] = '''<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="user-scalable=no, initial-scale=1.0, minimum-scale=1.0, maximum-scale=1.0, minimal-ui">
    <title>Ariadne GraphQL</title>
    <style>
      html, body {
        height: 100%;
        margin: 0;
        width: 100%;
        overflow: hidden;
      }
    </style>
  </head>
  <body>
    <div style="width: 100%; height: 100%;" id=\'embedded-sandbox\'></div>
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
  </body>
</html>
'''

snapshots['test_default_explorer_html_is_served_on_get_request 1'] = '''<!--
 *  Copyright (c) 2021 GraphQL Contributors
 *  All rights reserved.
 *
 *  This source code is licensed under the license found in the
 *  LICENSE file in the root directory of this source tree.
-->
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="user-scalable=no, initial-scale=1.0, minimum-scale=1.0, maximum-scale=1.0, minimal-ui">
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

      #graphiql-loading {
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;

        color: #545454;
        font-size: 1.5em;
        font-family: sans-serif;
        font-weight: bold;
      }
    </style>
    <link rel="stylesheet" href="https://unpkg.com/graphiql/graphiql.min.css" />
    
  </head>

  <body>
    <div id="graphiql">
      <div id="graphiql-loading">Loading Ariadne GraphQL...</div>
    </div>

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

      function AriadneGraphiQL() {
        var [query, setQuery] = React.useState(
          \'#\\n# GraphiQL is an in -browser tool for writing, validating, and\\n# testing GraphQL queries.\\n#\\n# Type queries into this side of the screen, and you will see intelligent\\n# typeaheads aware of the current GraphQL type schema and live syntax and\\n# validation errors highlighted within the text.\\n#\\n# GraphQL queries typically start with a "{" character. Lines that start\\n# with a # are ignored.\\n#\\n# An example GraphQL query might look like:\\n#\\n#     {\\n#       field(arg: "value") {\\n#         subField\\n#\\n#       }\\n#\\n#     }\\n#\\n# Keyboard shortcuts:\\n#\\n#   Prettify query: Shift - Ctrl - P(or press the prettify button)\\n#\\n#  Merge fragments: Shift - Ctrl - M(or press the merge button)\\n#\\n#        Run Query: Ctrl - Enter(or press the play button)\\n#\\n#    Auto Complete: Ctrl - Space(or just start typing)\\n#\',
        );
        
        return React.createElement(GraphiQL, {
          fetcher: fetcher,
          defaultEditorToolsVisibility: true,
          
          query: query,
          onEditQuery: setQuery,
        });
      }

      ReactDOM.render(
        React.createElement(AriadneGraphiQL),
        document.getElementById('graphiql'),
      );
    </script>
  </body>
</html>
'''

snapshots['test_graphiql_html_is_served_on_get_request 1'] = '''<!--
 *  Copyright (c) 2021 GraphQL Contributors
 *  All rights reserved.
 *
 *  This source code is licensed under the license found in the
 *  LICENSE file in the root directory of this source tree.
-->
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="user-scalable=no, initial-scale=1.0, minimum-scale=1.0, maximum-scale=1.0, minimal-ui">
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

      #graphiql-loading {
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;

        color: #545454;
        font-size: 1.5em;
        font-family: sans-serif;
        font-weight: bold;
      }
    </style>
    <link rel="stylesheet" href="https://unpkg.com/graphiql/graphiql.min.css" />
    
  </head>

  <body>
    <div id="graphiql">
      <div id="graphiql-loading">Loading Ariadne GraphQL...</div>
    </div>

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

      function AriadneGraphiQL() {
        var [query, setQuery] = React.useState(
          \'#\\n# GraphiQL is an in -browser tool for writing, validating, and\\n# testing GraphQL queries.\\n#\\n# Type queries into this side of the screen, and you will see intelligent\\n# typeaheads aware of the current GraphQL type schema and live syntax and\\n# validation errors highlighted within the text.\\n#\\n# GraphQL queries typically start with a "{" character. Lines that start\\n# with a # are ignored.\\n#\\n# An example GraphQL query might look like:\\n#\\n#     {\\n#       field(arg: "value") {\\n#         subField\\n#\\n#       }\\n#\\n#     }\\n#\\n# Keyboard shortcuts:\\n#\\n#   Prettify query: Shift - Ctrl - P(or press the prettify button)\\n#\\n#  Merge fragments: Shift - Ctrl - M(or press the merge button)\\n#\\n#        Run Query: Ctrl - Enter(or press the play button)\\n#\\n#    Auto Complete: Ctrl - Space(or just start typing)\\n#\',
        );
        
        return React.createElement(GraphiQL, {
          fetcher: fetcher,
          defaultEditorToolsVisibility: true,
          
          query: query,
          onEditQuery: setQuery,
        });
      }

      ReactDOM.render(
        React.createElement(AriadneGraphiQL),
        document.getElementById('graphiql'),
      );
    </script>
  </body>
</html>
'''

snapshots['test_playground_html_is_served_on_get_request 1'] = '''<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="user-scalable=no, initial-scale=1.0, minimum-scale=1.0, maximum-scale=1.0, minimal-ui">
    <title>Ariadne GraphQL</title>
    <link rel="stylesheet" href="//cdn.jsdelivr.net/npm/graphql-playground-react/build/static/css/index.css" />
    <link rel="shortcut icon" href="//cdn.jsdelivr.net/npm/graphql-playground-react/build/favicon.png" />
    <script src="//cdn.jsdelivr.net/npm/graphql-playground-react/build/static/js/middleware.js"></script>
  </head>
  <body>
    <div id="root">
      <style>
        body {
          background-color: rgb(23, 42, 58);
          font-family: Open Sans, sans-serif;
          height: 90vh;
        }

        #root {
          height: 100%;
          width: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .loading {
          font-size: 32px;
          font-weight: 200;
          color: rgba(255, 255, 255, .6);
          margin-left: 20px;
        }

        img {
          width: 78px;
          height: 78px;
        }

        .title {
          font-weight: 400;
        }
      </style>
      <img src='//cdn.jsdelivr.net/npm/graphql-playground-react/build/logo.png' alt=''>
      <div class="loading"> Loading
        <span class="title">Ariadne GraphQL</span>
      </div>
    </div>
    <script>
      window.addEventListener('load', function (event) {
        GraphQLPlayground.init(document.getElementById('root'), {
          // options as 'endpoint' belong here
          
        })
      })
    </script>
  </body>
</html>
'''

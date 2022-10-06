# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_graphiql_explorer_includes_explorer_plugin 1'] = '''<!--
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

  <!--
      This GraphiQL example depends on Promise and fetch, which are available in
      modern browsers, but can be "polyfilled" for older browsers.
      GraphiQL itself depends on React DOM.
      If you do not want to rely on a CDN, you can host these files locally or
      include them directly in your favored resource bundler.
    -->
  <script crossorigin src="https://unpkg.com/react@17/umd/react.development.js"></script>
  <script crossorigin src="https://unpkg.com/react-dom@17/umd/react-dom.development.js"></script>

  <!--
      These two files can be found in the npm module, however you may wish to
      copy them directly into your environment, or perhaps include them in your
      favored resource bundler.
     -->
  <link rel="stylesheet" href="https://unpkg.com/graphiql/graphiql.min.css" />
  
  <link rel="stylesheet" href="https://unpkg.com/@graphiql/plugin-explorer/dist/style.css" />
  
</head>

<body>
  <div id="graphiql">Loading Ariadne GraphQL...</div>
  <script src="https://unpkg.com/graphiql/graphiql.min.js" type="application/javascript"></script>
  
  <script crossorigin src="https://unpkg.com/@graphiql/plugin-explorer/dist/graphiql-plugin-explorer.umd.js" type="application/javascript"></script>
  
  <script type="application/javascript">
    var fetcher = GraphiQL.createFetcher({
      url: 'https://swapi-graphql.netlify.app/.netlify/functions/index',
    });
    var defaultQuery = "# Welcome to GraphiQL\\
#\\
# GraphiQL is an in -browser tool for writing, validating, and\\
# testing GraphQL queries.\\
#\\
# Type queries into this side of the screen, and you will see intelligent\\
# typeaheads aware of the current GraphQL type schema and live syntax and\\
# validation errors highlighted within the text.\\
#\\
# GraphQL queries typically start with a \\"{\\" character.Lines that start\\
# with a # are ignored.\\
#\\
# An example GraphQL query might look like:\\
#\\
#     {\\
#       field(arg: \\"value\\") {\\
#         subField\\
#\\
        }\\
#\\
      }\\
#\\
# Keyboard shortcuts:\\
#\\
#   Prettify query: Shift - Ctrl - P(or press the prettify button)\\
#\\
#  Merge fragments: Shift - Ctrl - M(or press the merge button)\\
#\\
#        Run Query: Ctrl - Enter(or press the play button)\\
#\\
#    Auto Complete: Ctrl - Space(or just start typing)\\
#";

    
    function GraphiQLWithExplorer() {
      var [query, setQuery] = React.useState(defaultQuery);
      var explorerPlugin = GraphiQLPluginExplorer.useExplorerPlugin({
        query: query,
        onEdit: setQuery,
      });
      return React.createElement(GraphiQL, {
        fetcher: fetcher,
        defaultEditorToolsVisibility: true,
        plugins: [explorerPlugin],
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
'''

snapshots['test_graphiql_explorer_produces_html 1'] = '''<!--
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

  <!--
      This GraphiQL example depends on Promise and fetch, which are available in
      modern browsers, but can be "polyfilled" for older browsers.
      GraphiQL itself depends on React DOM.
      If you do not want to rely on a CDN, you can host these files locally or
      include them directly in your favored resource bundler.
    -->
  <script crossorigin src="https://unpkg.com/react@17/umd/react.development.js"></script>
  <script crossorigin src="https://unpkg.com/react-dom@17/umd/react-dom.development.js"></script>

  <!--
      These two files can be found in the npm module, however you may wish to
      copy them directly into your environment, or perhaps include them in your
      favored resource bundler.
     -->
  <link rel="stylesheet" href="https://unpkg.com/graphiql/graphiql.min.css" />
  
</head>

<body>
  <div id="graphiql">Loading Ariadne GraphQL...</div>
  <script src="https://unpkg.com/graphiql/graphiql.min.js" type="application/javascript"></script>
  
  <script type="application/javascript">
    var fetcher = GraphiQL.createFetcher({
      url: 'https://swapi-graphql.netlify.app/.netlify/functions/index',
    });
    var defaultQuery = "# Welcome to GraphiQL\\
#\\
# GraphiQL is an in -browser tool for writing, validating, and\\
# testing GraphQL queries.\\
#\\
# Type queries into this side of the screen, and you will see intelligent\\
# typeaheads aware of the current GraphQL type schema and live syntax and\\
# validation errors highlighted within the text.\\
#\\
# GraphQL queries typically start with a \\"{\\" character.Lines that start\\
# with a # are ignored.\\
#\\
# An example GraphQL query might look like:\\
#\\
#     {\\
#       field(arg: \\"value\\") {\\
#         subField\\
#\\
        }\\
#\\
      }\\
#\\
# Keyboard shortcuts:\\
#\\
#   Prettify query: Shift - Ctrl - P(or press the prettify button)\\
#\\
#  Merge fragments: Shift - Ctrl - M(or press the merge button)\\
#\\
#        Run Query: Ctrl - Enter(or press the play button)\\
#\\
#    Auto Complete: Ctrl - Space(or just start typing)\\
#";

    
    ReactDOM.render(
      React.createElement(GraphiQL, {
        fetcher: fetcher,
        defaultEditorToolsVisibility: true,
        query: query,
      }),
      document.getElementById('graphiql'),
    );
    
  </script>
</body>

</html>
'''

snapshots['test_playground_explorer_produces_html 1'] = '''<!DOCTYPE html>
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
  <script>window.addEventListener('load', function (event) {
      GraphQLPlayground.init(document.getElementById('root'), {
        // options as 'endpoint' belong here
      })
    })</script>
</body>
</html>
'''

# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_playground_html_is_served_on_get_request 1'] = [
    b'<!--\n *  Copyright (c) 2021 GraphQL Contributors\n *  All rights reserved.\n *\n *  This source code is licensed under the license found in the\n *  LICENSE file in the root directory of this source tree.\n-->\n<!DOCTYPE html>\n<html>\n  <head>\n    <style>\n      body {\n        height: 100%;\n        margin: 0;\n        width: 100%;\n        overflow: hidden;\n      }\n\n      #graphiql {\n        height: 100vh;\n      }\n    </style>\n\n    <!--\n      This GraphiQL example depends on Promise and fetch, which are available in\n      modern browsers, but can be "polyfilled" for older browsers.\n      GraphiQL itself depends on React DOM.\n      If you do not want to rely on a CDN, you can host these files locally or\n      include them directly in your favored resource bundler.\n    -->\n    <script\n      crossorigin\n      src="https://unpkg.com/react@17/umd/react.development.js"\n    ></script>\n    <script\n      crossorigin\n      src="https://unpkg.com/react-dom@17/umd/react-dom.development.js"\n    ></script>\n\n    <!--\n      These two files can be found in the npm module, however you may wish to\n      copy them directly into your environment, or perhaps include them in your\n      favored resource bundler.\n     -->\n    <link rel="stylesheet" href="https://unpkg.com/graphiql/graphiql.min.css" />\n  </head>\n\n  <body>\n    <div id="graphiql">Loading...</div>\n    <script\n      src="https://unpkg.com/graphiql/graphiql.min.js"\n      type="application/javascript"\n    ></script>\n    <script>\n      ReactDOM.render(\n        React.createElement(GraphiQL, {\n          fetcher: GraphiQL.createFetcher({\n            url: \'https://swapi-graphql.netlify.app/.netlify/functions/index\',\n          }),\n          defaultEditorToolsVisibility: true,\n        }),\n        document.getElementById(\'graphiql\'),\n      );\n    </script>\n  </body>\n</html>'
]

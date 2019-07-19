from graphql import GraphQLResolveInfo, ResponsePath


def format_path(path: ResponsePath):
    elements = []
    while path:
        elements.append(path.key)
        path = path.prev
    return elements[::-1]


def should_trace(info: GraphQLResolveInfo):
    path = info.path
    while path:
        if isinstance(path.key, str) and path.key.startswith("__"):
            return False
        path = path.prev
    return True

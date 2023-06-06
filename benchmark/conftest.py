import pytest

from ariadne import gql


@pytest.fixture
def benchmark_query():
    return gql(
        """
    query GetThreads {
        threads {
            id
            category {
                id
                name
                slug
                color
                parent {
                    id
                    name
                    slug
                    color
                }
            }
            title
            slug
            starter {
                id
                handle
                slug
                name
                title
                group {
                    title
                }
            }
            starterName
            startedAt
            lastPoster {
                id
                handle
                slug
                name
                title
                group {
                    title
                }
            }
            lastPosterName
            lastPostedAt
            isClosed
            isHidden
            replies {
                ... ReplyData
                replies {
                    ... ReplyData
                }
            }
        }
    }

    fragment ReplyData on Post {
        id
        poster {
            id
            handle
            slug
            name
            title
            group {
                title
            }
        }
        postedAt
        content
        edits
    }
    """
    )

Mutations
=========

So far all examples in this documentation dealt with ``Query`` type and reading the data. What about creating, updating or deleting?

Enter the ``Mutation`` type, ``Query``'s sibling that GraphQL servers use to implement functions that change application state.

.. note::
   Because there is no restriction on what can be done inside resolvers, technically there's nothing stopping somebody from making ``Query`` fields act as mutations, taking inputs and executing state-changing logic.

   In practice such queries break the contract with client libraries such as Apollo-Client that do client-side caching and state management, resulting in non-responsive controls or inaccurate information being displayed in the UI as library displays cached data before redrawing to display actual response from the GraphQL.


Defining mutations
------------------

Lets define basic schema that implements simple authentication mechanism allowing client to see if they are authenticated, log in and log out::

    type_def = """
        type Query {
            isAuthenticated: Boolean!
        }

        type Mutation {
            login(username: String!, password: String!): Boolean!
            logout: Boolean!
        }
    """

In this example we have following elements:

``Query`` type with single field: boolean for checking if we are authenticated or not. It may appear superficial for sake of this example, *but Ariadne requires* that your GraphQL API always defines ``Query`` type.

``Mutation`` type with two mutations: ``login`` mutation that requires username and password strings and returns bool with status, and ``logout`` that takes no arguments and just returns status.

For simplicity sake our mutations return bools, but really there is no such restriction. You can have resolver that returns status code, updated object, or error message::

    type_def = """
        type Mutation {
            login(username: String!, password: String!) {
                status: String!
                error: Error
                user: User
            }
        }
    """


Writing resolvers
-----------------

Mutation resolvers are no different to resolvers used by other types. They are functions that take ``parent`` and ``info`` arguments, as well as any mutation's arguments as keyword arguments. They then return data that should be sent to client as query's result::

    def resolve_login(_, info, username, password):
        request = info.context["request"]
        user = auth.authenticate(username, password)
        if user:
            auth.login(request, user)
            return True
        return False


    def resolve_logout(_, info):
        request = info.context["request"]
        if request.user.is_authenticated:
            auth.logout(request)
            return True
        return False

Because ``Mutation`` is GraphQL type like others, you can map resolvers to mutations using dict::

    resolvers {
        "Mutation": {
            "login": resolve_login,
            "logout": resolve_logout,
        }
    }


Inputs
------

Let's consider following type::

    type_def = """
        type Discussion {
            category: Category!
            poster: User
            postedOn: Date!
            title: String!
            isAnnouncement: Boolean!
            isClosed: Boolean!
        }
    """

Imagine mutation for creating ``Discussion`` that takes category, poster, title, announcement and closed states as inputs, and creates new ``Discussion`` in database. Looking at previous example, we may want that define it like this::

    type_def = """
        type Mutation {
            createDiscussion(category: ID!, title: String!, isAnnouncement: Boolean, isClosed: Boolean) {
                status: Boolean!
                error: Error
                discussion: Discussion
            }
        }
    """

Our mutation takes only four arguments, but its already too unwieldy to work with. Imagine adding another one or two arguments to it in future, its going to explode!

GraphQL provides better way for solving this problem: ``input`` that allows us to move arguments into dedicated type::

    type_def = """
        type Mutation {
            createDiscussion(input: DiscussionInput!) {
                status: Boolean!
                error: Error
                discussion: Discussion
            }
        }

        input DiscussionInput {
            category: ID!
            title: String!,
            isAnnouncement: Boolean
            isClosed: Boolean
        }
    """

Now when client would want to create new discussion, they need to provide ``input`` object that matches the ``DiscussionInput`` definition. This input will then be validated and passed to mutation's resolver as dict available under the ``input`` keyword argument::

    def resolve_create_discussion(_, info, input):
        clean_input = {
            "category": input["category"],
            "title": input["title"],
            "is_announcement": input.get("isAnnouncement"),
            "is_closed": input.get("isClosed"),
        }

        try:
            return {
                "status": True,
                "discussion": create_new_discussion(info.context, clean_input),
            }
        except ValidationError as err:
            return {
                "status": False,
                "error: err,
            }

Other advantage of ``input``s is that they are reusable. If we'll later decide to implement another mutation, for updating the Discussion, we can do it like this::

    type_def = """
        type Mutation {
            createDiscussion(input: DiscussionInput!) {
                status: Boolean!
                error: Error
                discussion: Discussion
            }
            updateDiscussion(discussion: ID!, input: DiscussionInput!) {
                status: Boolean!
                error: Error
                discussion: Discussion
            }
        }

        input DiscussionInput {
            category: ID!
            title: String!,
            isAnnouncement: Boolean
            isClosed: Boolean
        }
    """

Our ``updateDiscussion`` mutation will now accept two arguments: ``discussion`` and ``input``::

    def resolve_update_discussion(_, info, discussion, input):
        clean_input = {
            "category": input["category"],
            "title": input["title"],
            "is_announcement": input.get("isAnnouncement"),
            "is_closed": input.get("isClosed"),
        }

        try:
            return {
                "status": True,
                "discussion": update_discussion(info.context, discussion, clean_input),
            }
        except ValidationError as err:
            return {
                "status": False,
                "error: err,
            }

You may wonder what would you want to use ``input`` instead of reusing already defined type. This is because input types provide some guarantees that regular objects don't: they are serializable, they don't implement interfaces or unions. However input fields are not limited to scalars. You can create fields that are lists, or even reference other inputs::

    type_def = """
        input PollInput {
            question: String!,
            options: [PollOptionInput!]!
        }

        input PollOptionInput {
            label: String!
            color: String!
        }
    """

Lastly, take note that inputs are not specific to mutations. You can create inputs to implement complex filtering in your ``Query`` fields.
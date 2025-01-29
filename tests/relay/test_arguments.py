from ariadne.contrib.relay.arguments import (
    BackwardConnectionArguments,
    ConnectionArguments,
    ForwardConnectionArguments,
)


def test_connection_arguments():
    connection_arguments = ConnectionArguments(
        first=10, after="cursor", last=5, before="cursor"
    )
    assert connection_arguments.first == 10
    assert connection_arguments.after == "cursor"
    assert connection_arguments.last == 5
    assert connection_arguments.before == "cursor"


def test_forward_connection_arguments():
    connection_arguments = ForwardConnectionArguments(first=10, after="cursor")
    assert connection_arguments.first == 10
    assert connection_arguments.after == "cursor"


def test_backward_connection_arguments():
    connection_arguments = BackwardConnectionArguments(last=5, before="cursor")
    assert connection_arguments.last == 5
    assert connection_arguments.before == "cursor"

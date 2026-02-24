from collections import namedtuple
from collections.abc import Callable
from typing import TypeVar

from ariadne.contrib.relay.connection import RelayConnection

ConnectionResolver = TypeVar("ConnectionResolver", bound=Callable[..., RelayConnection])
GlobalIDTuple = namedtuple("GlobalIDTuple", ["type", "id"])
GlobalIDDecoder = Callable[[str], GlobalIDTuple]
GlobalIDEncoder = Callable[[str, str], str]

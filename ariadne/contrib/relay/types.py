from collections import namedtuple
from typing import Any, Callable, Dict

from typing_extensions import TypeVar

from ariadne.contrib.relay.connection import RelayConnection

ConnectionResolver = TypeVar("ConnectionResolver", bound=Callable[..., RelayConnection])
GlobalIDTuple = namedtuple("GlobalIDTuple", ["type", "id"])
GlobalIDDecoder = Callable[[Dict[str, Any]], GlobalIDTuple]

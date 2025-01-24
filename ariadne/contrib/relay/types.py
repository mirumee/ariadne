from typing import Callable

from typing_extensions import TypeVar

from ariadne.contrib.relay.connection import RelayConnection

ConnectionResolver = TypeVar("ConnectionResolver", bound=Callable[..., RelayConnection])

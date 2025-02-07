from base64 import b64decode, b64encode

from ariadne.contrib.relay.types import (
    GlobalIDTuple,
)


def decode_global_id(gid: str) -> GlobalIDTuple:
    return GlobalIDTuple(*b64decode(gid).decode().split(":"))


def encode_global_id(type_name: str, _id: str) -> str:
    return b64encode(f"{type_name}:{_id}".encode()).decode()

from ariadne.contrib.relay import (
    GlobalIDTuple,
    decode_global_id,
    encode_global_id,
)


def test_decode_global_id():
    assert decode_global_id("VXNlcjox") == GlobalIDTuple("User", "1")


def test_encode_global_id():
    assert encode_global_id("User", "1") == "VXNlcjox"

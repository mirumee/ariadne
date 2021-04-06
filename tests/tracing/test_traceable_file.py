import cgi
import pytest

from starlette.datastructures import UploadFile

from ariadne.contrib.tracing.traceable_file import TraceableFile


def test_traceable_file_properties_upload_file():
    filename = "hello.txt"
    content_type = "text/plain"
    traceable_file = TraceableFile(UploadFile(filename, content_type=content_type))
    assert traceable_file.filename == filename
    assert traceable_file.content_type == content_type
    assert traceable_file.size == 0


@pytest.mark.parametrize("payload, expected", [("111", 3), (None, 0)])
def test_traceable_file_properties_field_storage(payload, expected):
    filename = "hello.txt"
    content_type = "text/plain"
    field_storage = cgi.FieldStorage()
    field_storage.type = content_type
    field_storage.filename = filename
    field_storage.value = payload
    traceable_file = TraceableFile(field_storage)

    assert traceable_file.content_type == content_type
    assert traceable_file.filename == filename
    assert traceable_file.size == expected

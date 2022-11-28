from io import BytesIO


def create_multipart_request(data):
    return {
        "PATH_INFO": "/graphql/",
        "REQUEST_METHOD": "POST",
        "CONTENT_TYPE": (
            "multipart/form-data; boundary=------------------------cec8e8123c05ba25"
        ),
        "CONTENT_LENGTH": len(data),
        "wsgi.input": BytesIO(data.encode("latin-1")),
    }

import os
import cgi

from typing import Optional, Union, Dict, Any
from starlette.datastructures import UploadFile


class TraceableFile:
    def __init__(self, upload_file: Union[UploadFile, cgi.FieldStorage]) -> None:
        self._upload_file = upload_file

    def __deepcopy__(self, _: Dict[int, Any]) -> str:
        return (
            f"{type(self._upload_file)}"
            f"(name: {self.filename}, type: {self.content_type}, size: {self.size})"
        )

    @property
    def filename(self) -> Optional[str]:
        return (
            self._upload_file.filename
            if isinstance(self._upload_file, cgi.FieldStorage)
            else self._upload_file.filename
        )

    @property
    def content_type(self) -> str:
        return (
            self._upload_file.type
            if isinstance(self._upload_file, cgi.FieldStorage)
            else self._upload_file.content_type
        )

    @property
    def size(self) -> int:
        if self._upload_file.file is None and isinstance(
            self._upload_file, cgi.FieldStorage
        ):
            return (
                len(self._upload_file.value)
                if self._upload_file.value is not None
                else 0
            )

        file_ = self._upload_file.file
        file_.seek(0, os.SEEK_END)
        size = file_.tell()
        file_.seek(0)

        return size

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class RomEntry:
    source_id: str = ""
    file_path: str = ""
    size: int = 0
    md5: str = ""
    crc32: str = ""
    sha1: str = ""
    format: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> RomEntry:
        return cls(
            source_id=data.get("source_id", ""),
            file_path=data.get("file_path", ""),
            size=int(data.get("size", 0)),
            md5=data.get("md5", ""),
            crc32=data.get("crc32", ""),
            sha1=data.get("sha1", ""),
            format=data.get("format", ""),
        )

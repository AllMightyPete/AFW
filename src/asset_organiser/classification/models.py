from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class FileEntry(BaseModel):
    filename: str
    filetype: Optional[str] = None


class AssetEntry(BaseModel):
    asset_type: Optional[str] = None
    asset_tags: List[str] = Field(default_factory=list)
    asset_contents: List[str] = Field(default_factory=list)


class SourceData(BaseModel):
    metadata: Dict[str, object] = Field(default_factory=dict)
    contents: Dict[str, FileEntry] = Field(default_factory=dict)
    assets: Dict[str, AssetEntry] = Field(default_factory=dict)


class ClassificationState(BaseModel):
    sources: Dict[str, SourceData] = Field(default_factory=dict)

    @classmethod
    def from_json(cls, text: str) -> "ClassificationState":
        return cls.model_validate_json(text)

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import StrEnum
from datetime import datetime


def get_markdown_safe_text(s: str) -> str:
    s = s.strip().lower().replace(' ', '-')

    # Allow only markdown characters in hyperlink
    s = ''.join(c for c in s if c.isalnum() or c in ['-', '_'])

    return s


def get_markdown_hyperlink(text: str) -> str:
    hyperlink = get_markdown_safe_text(text)

    return f"[{text}](#{hyperlink})"


def dict_to_struct(data: dict, struct_type: type) -> BaseModel:
    return struct_type(**data)


def struct_to_dict(data: BaseModel) -> dict:
    return data.model_dump()


class TextEditor(StrEnum):
    NANO = "nano"
    VIM = "vim"
    NOTEPAD = "notepad"


class Collection(BaseModel):
    id: int
    name: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


class Tag(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    @property
    def md_link(self):
        return get_markdown_hyperlink(self.description)


class Paragraph(BaseModel):
    id: int
    title: str
    content: str
    collection: Optional[Collection] = None
    tags: List[Tag] = Field(default_factory= [])
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    @property
    def md_link(self):
        return get_markdown_hyperlink(self.title)
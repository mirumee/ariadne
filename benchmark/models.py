from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class RoleEnum(str, Enum):
    SEE = "SEE"
    BROWSE = "BROWSE"
    START = "START"
    REPLY = "REPLY"
    MODERATE = "MODERATE"


class UserStatusEnum(str, Enum):
    OFFLINE = "OFFLINE"
    ONLINE = "ONLINE"
    BANNED = "BANNED"


@dataclass
class GroupModel:
    id: int
    name: str
    slug: str
    title: str | None
    roles: list[RoleEnum]


@dataclass
class UserModel:
    id: int
    handle: str
    slug: str
    name: str | None
    title: str | None
    email: str
    group_id: int
    groups: list[int]
    avatar_images: list[dict]
    status: UserStatusEnum
    posts: int
    joined_at: datetime


@dataclass
class CategoryModel:
    id: int
    name: str
    slug: str
    color: str
    parent_id: int | None


@dataclass
class ThreadModel:
    id: int
    category_id: int
    title: str
    slug: str
    starter_id: int | None
    starter_name: str
    started_at: datetime
    last_poster_id: int | None
    last_poster_name: str
    last_posted_at: datetime
    is_closed: bool
    is_hidden: bool


@dataclass
class PostModel:
    id: int
    thread_id: int
    category_id: int
    parent_id: int | None
    poster_id: int | None
    poster_name: str
    posted_at: datetime
    content: list[dict]
    edits: int

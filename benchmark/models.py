from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
from datetime import datetime


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
    title: Optional[str]
    roles: List[RoleEnum]


@dataclass
class UserModel:
    id: int
    handle: str
    slug: str
    name: Optional[str]
    title: Optional[str]
    email: str
    group_id: int
    groups: List[int]
    avatar_images: List[dict]
    status: UserStatusEnum
    posts: int
    joined_at: datetime


@dataclass
class CategoryModel:
    id: int
    name: str
    slug: str
    color: str
    parent_id: Optional[int]


@dataclass
class ThreadModel:
    id: int
    category_id: int
    title: str
    slug: str
    starter_id: Optional[int]
    starter_name: str
    started_at: datetime
    last_poster_id: Optional[int]
    last_poster_name: str
    last_posted_at: datetime
    is_closed: bool
    is_hidden: bool


@dataclass
class PostModel:
    id: int
    thread_id: int
    category_id: int
    parent_id: Optional[int]
    poster_id: Optional[int]
    poster_name: str
    posted_at: datetime
    content: List[dict]
    edits: int

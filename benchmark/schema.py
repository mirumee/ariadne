from datetime import datetime
from typing import Optional

from ariadne import (
    EnumType,
    ObjectType,
    QueryType,
    ScalarType,
    load_schema_from_path,
    make_executable_schema,
)

from .conf import SCHEMA_PATH
from .database import database
from .models import (
    CategoryModel,
    GroupModel,
    PostModel,
    RoleEnum,
    ThreadModel,
    UserModel,
    UserStatusEnum,
)

datetime_scalar = ScalarType("DateTime")


@datetime_scalar.serializer
def serialize_datetime(value: datetime) -> str:
    return value.isoformat()


type_defs = load_schema_from_path(SCHEMA_PATH)

query_type = QueryType()


@query_type.field("category")
async def resolve_category(*_, id: str) -> Optional[CategoryModel]:
    return await database.fetch_one("category", id=int(id))


@query_type.field("categories")
async def resolve_categories(*_, id: Optional[list[str]] = None) -> list[CategoryModel]:
    if id:
        categories_ids = [int(i) for i in id]
        return await database.fetch_all("category", id__in=categories_ids)

    return await database.fetch_all("category", parent_id=None)


@query_type.field("thread")
async def resolve_thread(*_, id: str) -> Optional[ThreadModel]:
    return await database.fetch_one("thread", id=int(id))


@query_type.field("threads")
async def resolve_threads(
    *_,
    category: Optional[str] = None,
    starter: Optional[str] = None,
) -> list[ThreadModel]:
    filters = {}
    if category:
        filters["category_id"] = int(category)
    if starter:
        filters["starter_id"] = int(starter)

    return await database.fetch_all("thread", **filters)


@query_type.field("post")
async def resolve_post(*_, id: str) -> Optional[PostModel]:
    return await database.fetch_one("post", id=int(id))


@query_type.field("groups")
async def resolve_groups(*_) -> list[GroupModel]:
    return await database.fetch_all("group")


@query_type.field("group")
async def resolve_group(*_, id: str) -> Optional[GroupModel]:
    return await database.fetch_one("group", id=int(id))


@query_type.field("users")
async def resolve_users(*_, id: str) -> list[UserModel]:
    return await database.fetch_all("user")


@query_type.field("user")
async def resolve_user(*_, id: str) -> Optional[UserModel]:
    return await database.fetch_one("user", id=int(id))


category_type = ObjectType("Category")


@category_type.field("parent")
async def resolve_category_parent(obj: CategoryModel, info) -> Optional[CategoryModel]:
    if not obj.parent_id:
        return None

    return await database.fetch_one("category", id=obj.parent_id)


@category_type.field("children")
async def resolve_category_children(obj: CategoryModel, info) -> list[CategoryModel]:
    return await database.fetch_all("category", parent_id=obj.id)


thread_type = ObjectType("Thread")

thread_type.set_alias("starterName", "starter_name")
thread_type.set_alias("startedAt", "started_at")
thread_type.set_alias("lastPosterName", "last_poster_name")
thread_type.set_alias("lastPostedAt", "last_posted_at")
thread_type.set_alias("isClosed", "is_closed")
thread_type.set_alias("isHidden", "is_hidden")


@thread_type.field("category")
async def resolve_thread_category(obj: ThreadModel, info) -> Optional[CategoryModel]:
    return await database.fetch_one("category", id=obj.category_id)


@thread_type.field("starter")
async def resolve_thread_starter(obj: ThreadModel, info) -> Optional[UserModel]:
    if not obj.starter_id:
        return None

    return await database.fetch_one("user", id=obj.starter_id)


@thread_type.field("lastPoster")
async def resolve_thread_last_poster(obj: ThreadModel, info) -> Optional[UserModel]:
    if not obj.last_poster_id:
        return None

    return await database.fetch_one("user", id=obj.last_poster_id)


@thread_type.field("replies")
async def resolve_thread_replies(obj: ThreadModel, info) -> list[PostModel]:
    return await database.fetch_all("post", thread_id=obj.id, parent_id=None)


post_type = ObjectType("Post")

post_type.set_alias("posterName", "poster_name")
post_type.set_alias("postedAt", "posted_at")


@post_type.field("thread")
async def resolve_post_thread(obj: PostModel, info) -> ThreadModel:
    return await database.fetch_one("thread", id=obj.thread_id)


@post_type.field("category")
async def resolve_post_category(obj: PostModel, info) -> CategoryModel:
    return await database.fetch_one("category", id=obj.category_id)


@post_type.field("poster")
async def resolve_post_poster(obj: PostModel, info) -> Optional[UserModel]:
    if not obj.poster_id:
        return None

    return await database.fetch_one("user", id=obj.poster_id)


@post_type.field("parent")
async def resolve_post_parent(obj: PostModel, info) -> Optional[PostModel]:
    if not obj.parent_id:
        return None

    return await database.fetch_one("post", id=obj.parent_id)


@post_type.field("replies")
async def resolve_post_replies(obj: PostModel, info) -> list[PostModel]:
    return await database.fetch_all("post", parent_id=obj.id)


group_type = ObjectType("Group")


@group_type.field("members")
async def resolve_group_members(obj: GroupModel, info) -> list[UserModel]:
    return await database.fetch_all("user", group_id=obj.id)


user_type = ObjectType("User")

user_type.set_alias("joinedAt", "joined_at")


@user_type.field("group")
async def resolve_user_group(obj: UserModel, info) -> GroupModel:
    return await database.fetch_all("group", id=obj.group_id)


@user_type.field("groups")
async def resolve_user_groups(obj: UserModel, info) -> list[GroupModel]:
    return await database.fetch_all("group", id__in=obj.groups)


schema = make_executable_schema(
    type_defs,
    datetime_scalar,
    query_type,
    category_type,
    thread_type,
    post_type,
    group_type,
    user_type,
    EnumType("Role", RoleEnum),
    EnumType("UserStatus", UserStatusEnum),
)

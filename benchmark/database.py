import json
from datetime import datetime

from .conf import DATABASE_PATH
from .models import (
    CategoryModel,
    GroupModel,
    PostModel,
    RoleEnum,
    ThreadModel,
    UserModel,
    UserStatusEnum,
)


class Database:
    data: dict

    def __init__(self):
        with open(DATABASE_PATH) as fp:
            raw_data = json.load(fp)

        self.data = {}
        for table_name in raw_data:
            self.data[table_name] = []

        for category_data in raw_data["category"]:
            self.data["category"].append(CategoryModel(**category_data))

        for thread_data in raw_data["thread"]:
            thread_data["started_at"] = datetime.fromisoformat(
                thread_data["started_at"]
            )
            thread_data["last_posted_at"] = datetime.fromisoformat(
                thread_data["last_posted_at"]
            )

            self.data["thread"].append(ThreadModel(**thread_data))

        for post_data in raw_data["post"]:
            post_data["posted_at"] = datetime.fromisoformat(post_data["posted_at"])

            self.data["post"].append(PostModel(**post_data))

        for group_data in raw_data["group"]:
            group_data["roles"] = [RoleEnum(role) for role in group_data["roles"]]

            self.data["group"].append(GroupModel(**group_data))

        for user_data in raw_data["user"]:
            user_data["joined_at"] = datetime.fromisoformat(user_data["joined_at"])
            user_data["status"] = UserStatusEnum(user_data["status"])

            self.data["user"].append(UserModel(**user_data))

    async def fetch_one(self, table: str, **filters):
        if table not in self.data:
            raise ValueError(f"Unknown table: '{table}'")

        for row in self.data[table]:
            if match_row(row, filters):
                return row

    async def fetch_all(self, table: str, **filters):
        if table not in self.data:
            raise ValueError(f"Unknown table: '{table}'")

        if not filters:
            return self.data[table]

        rows = []
        for row in self.data[table]:
            if match_row(row, filters):
                rows.append(row)

        return rows


def match_row(row, filters):
    for field, value in filters.items():
        if field.endswith("__in"):
            if getattr(row, field[:-4]) not in value:
                return False
        else:
            if getattr(row, field) != value:
                return False

    return True


database = Database()

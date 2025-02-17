import json
import random
from datetime import datetime
from typing import Optional

try:
    from faker import Faker
except ImportError as exc:
    raise ImportError("Faker is required! Run pip install Faker") from exc

from conf import DATABASE_PATH, SCHEMA_PATH

from ariadne import load_schema_from_path, make_executable_schema

fake = Faker()

GROUPS_COUNT = 10
USERS_COUNT = 100
CATEGORY_COUNT = 18
SUBCATEGORY_COUNT = 42
THREAD_COUNT = 200
POST_COUNT = 400
REPLY_COUNT = 700

AVATAR_SIZE = [400, 200, 128, 100, 64, 32, 24]


schema = make_executable_schema(load_schema_from_path(SCHEMA_PATH))

ROLES = list(schema.type_map["Role"].values)
USER_STATUS = list(schema.type_map["UserStatus"].values)


def main():
    database = {
        "group": [],
        "user": [],
        "category": [],
        "thread": [],
        "post": [],
    }

    db_id = 0
    for _ in range(GROUPS_COUNT):
        db_id += random.randint(1, 100)
        generate_group(database, db_id)

    db_id = 0
    for _ in range(USERS_COUNT):
        db_id += random.randint(1, 100)
        generate_user(database, db_id)

    db_id = 0
    for _ in range(CATEGORY_COUNT):
        db_id += random.randint(1, 100)
        generate_category(database, db_id)

    categories_ids = [category["id"] for category in database["category"]]
    for _ in range(SUBCATEGORY_COUNT):
        db_id += random.randint(1, 100)
        generate_category(database, db_id, random.choice(categories_ids))

    db_id = 0
    for _ in range(THREAD_COUNT):
        db_id += random.randint(1, 100)
        generate_thread(database, db_id)

    db_id = 0
    for _ in range(POST_COUNT):
        db_id += random.randint(1, 100)
        generate_post(database, db_id)

    posts_ids = [post["id"] for post in database["post"]]
    for _ in range(REPLY_COUNT):
        db_id += random.randint(1, 100)
        generate_post(database, db_id, random.choice(posts_ids))

    with open(DATABASE_PATH, "w") as fp:
        json.dump(database, fp, indent=2)


def generate_group(database: dict, db_id: int):
    roles = random.choices(ROLES, k=random.randint(1, len(ROLES)))

    title = None
    if random.randint(1, 100) < 30:
        title = fake.sentence(random.randint(1, 2)).rstrip(".")

    name = fake.sentence(random.randint(1, 2)).rstrip(".")

    database["group"].append(
        {
            "id": db_id,
            "name": name,
            "slug": name.lower().replace(" ", "-"),
            "title": title,
            "roles": sorted(set(roles)),
        }
    )


def generate_user(database: dict, db_id: int):
    name = None
    if random.randint(1, 100) < 70:
        name = fake.name()

    title = None
    if random.randint(1, 100) < 20:
        title = fake.sentence(random.randint(1, 2)).rstrip(".")

    main_group = random.choice(database["group"])["id"]
    groups = [main_group]
    if random.randint(1, 100) < 30:
        for _ in range(random.randint(1, 4)):
            groups.append(random.choice(database["group"])["id"])

    avatar_images = []
    for size in AVATAR_SIZE:
        avatar_images.append(
            {
                "size": size,
                "url": f"/avatar/{db_id}/{size}.png",
            }
        )

    handle = fake.user_name()

    database["user"].append(
        {
            "id": db_id,
            "handle": handle,
            "slug": slugify(handle),
            "name": name,
            "title": title,
            "email": fake.safe_email(),
            "group_id": main_group,
            "groups": sorted(groups),
            "avatar_images": avatar_images,
            "status": random.choice(USER_STATUS),
            "posts": random.randint(1, 10000),
            "joined_at": datetime.now().isoformat(),
        }
    )


def generate_category(database: dict, db_id: int, parent_id: Optional[int] = None):
    name = fake.sentence(random.randint(1, 3)).rstrip(".")

    database["category"].append(
        {
            "id": db_id,
            "name": name,
            "slug": slugify(name),
            "color": fake.color(),
            "parent_id": parent_id,
        }
    )


def generate_thread(database: dict, db_id: int):
    title = fake.sentence(random.randint(1, 15)).rstrip(".")

    if random.randint(1, 100) < 80:
        user = random.choice(database["user"])
        starter_id = user["id"]
        starter_name = user["handle"]
    else:
        starter_id = None
        starter_name = fake.user_name()

    if random.randint(1, 100) < 80:
        user = random.choice(database["user"])
        last_poster_id = user["id"]
        last_poster_name = user["handle"]
    else:
        last_poster_id = None
        last_poster_name = fake.user_name()

    database["thread"].append(
        {
            "id": db_id,
            "category_id": random.choice(database["category"])["id"],
            "title": title,
            "slug": slugify(title),
            "starter_id": starter_id,
            "starter_name": starter_name,
            "started_at": datetime.now().isoformat(),
            "last_poster_id": last_poster_id,
            "last_poster_name": last_poster_name,
            "last_posted_at": datetime.now().isoformat(),
            "is_closed": random.randint(1, 100) > 80,
            "is_hidden": random.randint(1, 100) > 90,
        }
    )


def generate_post(database: dict, db_id: int, parent_id: Optional[int] = None):
    thread = random.choice(database["thread"])

    if random.randint(1, 100) < 80:
        user = random.choice(database["user"])
        poster_id = user["id"]
        poster_name = user["handle"]
    else:
        poster_id = None
        poster_name = fake.user_name()

    database["post"].append(
        {
            "id": db_id,
            "thread_id": thread["id"],
            "category_id": thread["category_id"],
            "parent_id": parent_id,
            "poster_id": poster_id,
            "poster_name": poster_name,
            "posted_at": datetime.now().isoformat(),
            "content": generate_content(),
            "edits": random.randint(1, 15) if random.randint(1, 100) > 50 else 0,
        }
    )


def generate_content():
    content = []
    for _ in range(random.randint(1, 5)):
        if random.randint(1, 100) < 75:
            content.append(
                {
                    "id": fake.md5()[:8],
                    "type": "p",
                    "body": fake.paragraph(),
                }
            )
        else:
            content.append(
                {
                    "id": fake.md5()[:8],
                    "type": "img",
                    "img": fake.image_url(),
                }
            )

    return content


def slugify(value: str) -> str:
    return value.lower().replace(" ", "-")


if __name__ == "__main__":
    main()

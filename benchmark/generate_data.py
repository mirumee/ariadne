import json
import random
import string
from typing import List, Tuple


def make_random_complex_query(n: int) -> List[Tuple]:
    ROLES = ["SEE", "BROWSE", "START", "REPLY", "MODERATE"]
    complex_query = []

    for i in range(n):
        id = i
        name = "".join(random.sample(string.ascii_letters, 10))
        group = {
            "name": "".join(random.sample(string.ascii_letters, 3)),
            "roles": [random.choice(ROLES)],
        }
        avatar = [
            {
                "size": random.randint(1, 200),
                "url": "".join(random.sample(string.ascii_letters, 10)),
            }
        ]
        complex_query.append({"id": id, "name": name, "group": group, "avatar": avatar})
    return {"users": complex_query}


with open("benchmarks/data.json", "w") as complex_file:
    complex_file.write(json.dumps(make_random_complex_query(500), indent=2))

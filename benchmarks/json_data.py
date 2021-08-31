import json
import random
import string

from typing import List, Tuple


def make_random_simple_query(n: int) -> List[Tuple]:
    people_list = []
    for _ in range(n):
        generate_name = random.sample(string.ascii_letters, 10)
        name = "".join(generate_name)
        age = random.randint(1, 99)
        people_list.append({"name": name, "age": age})
    return people_list


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
    return complex_query


with open("benchmarks/simple.json", "w") as simple_file:
    simple_file.write(json.dumps(make_random_simple_query(500), indent=2))

with open("benchmarks/complex.json", "w") as complex_file:
    complex_file.write(json.dumps(make_random_complex_query(500), indent=2))

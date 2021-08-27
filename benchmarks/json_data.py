import json
import random
import string

from typing import List, Tuple



def make_random_name_and_age(n: int) -> List[Tuple]:
    people_list = []
    for _ in range(n):
        generate_name = random.sample(string.ascii_letters, 10)
        name = "".join(generate_name)
        age = random.randint(1, 99)
        people_list.append({"name": name, "age": age})
    return people_list

f = open('simple.json',"w")
with open('benchmarks/simple.json','w') as file:
    file.write(json.dumps(make_random_name_and_age(500),indent=2))


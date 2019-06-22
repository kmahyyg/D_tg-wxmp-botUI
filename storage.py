from typing import List

_storage = {}

def get(*args: List[str]):
    current = _storage
    for key in args:
        current = current[key]
    return current

def put(*args: List):
    assert(len(args) >= 2)
    current = _storage
    for index in range(len(args) - 2):
        key = args[index]
        if current.get(key) is None:
            current[key] = {}
        current = current[key]
    current[args[-2]] = args[-1]

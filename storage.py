_storage = {}


def get(*args):
    current = _storage
    for key in args:
        current = current[key]
    return current


def put(*args):
    assert (len(args) >= 2)
    current = _storage
    for index in range(len(args) - 2):
        key = args[index]
        if current.get(key) is None:
            current[key] = {}
        current = current[key]
    current[args[-2]] = args[-1]

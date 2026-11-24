from hashlib import sha256
import json


def serialize(value):
    return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'))


def digest(raw):
    return sha256(raw).hexdigest()


def lock(value):
    return digest(serialize(value).encode())

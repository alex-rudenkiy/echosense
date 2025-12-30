import redis

r = redis.Redis(host='127.0.0.1', port=6379, db=0)

def save_image_to_redis(task_id: str, image_bytes: bytes):
    key = f"image:{task_id}"
    r.set(key, image_bytes)
    r.expire(key, 3600)  # auto-expire через час

def get_image_from_redis(task_id: str) -> bytes:
    key = f"image:{task_id}"
    return r.get(key)

import redis
from redis.exceptions import ConnectionError

r = redis.Redis(host='redis', port=6379, db=0, decode_responses=False)

def save_image_to_redis(task_id: str, image_bytes: bytes, ttl: int = 3600):
    key = f"image:{task_id}"
    try:
        r.set(key, image_bytes)
        r.expire(key, ttl)
    except ConnectionError as e:
        raise RuntimeError(f"Failed to save image to Redis: {e}")

def get_image_from_redis(task_id: str) -> bytes:
    key = f"image:{task_id}"
    try:
        image_bytes = r.get(key)
        if image_bytes is None:
            raise ValueError(f"Image {task_id} not found in Redis")
        return image_bytes
    except ConnectionError as e:
        raise RuntimeError(f"Failed to get image from Redis: {e}")
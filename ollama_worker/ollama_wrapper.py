import base64
import httpx
from .redis_utils import get_image_from_redis
import logging
from uuid import uuid4

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def describe_image(img_id: str) -> str:
    try:
        image_bytes = get_image_from_redis(img_id)
        print(img_id, len(image_bytes))
        tmpfilename = str(uuid4())+'.dat'
        with open(tmpfilename, 'w') as f:
            print(tmpfilename)
            encoded_string = base64.b64encode(image_bytes).decode('utf-8')

            with httpx.Client(timeout=60.0) as client:
                # Опишите в свободной форме то, что вы видите на картинке, но отвечайте только по-русски и переведите все английские сокращения на русский язык
                prompt = f"Опишите на русском языке в свободной форме то, что вы видите на изображении."
                # print(prompt, encoded_string)

                response = client.post(
                    "http://...:11434/api/generate",
                    json={
                        "model": "gemma3:4b",
                        "prompt": prompt,
                        "stream": False,
                        "options": {"num_predict": 250},
                        "images": [encoded_string]
                    }
                )
                response.raise_for_status()
                return response.json()["response"]
    except Exception as e:
        logger.error(f"Failed to process image {img_id}: {e}")
        raise

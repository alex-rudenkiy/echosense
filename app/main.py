import logging
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from redis_utils import save_image_to_redis
from tasks import process_image_with_ollama, process_text_for_tts
import uuid
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI()

@app.post("/image-to-speech")
async def process_image(file: UploadFile = File(...)):
    img_id = str(uuid.uuid4())
    image_bytes = await file.read()

    # Сохраняем в Redis с увеличенным TTL
    save_image_to_redis(img_id, image_bytes, ttl=7200)  # 2 часа

    # Асинхронно запускаем задачу Ollama
    ollama_task = process_image_with_ollama.delay(img_id)
    
    try:
        # Ждем результат с повторными попытками
        description = await asyncio.wait_for(
            asyncio.to_thread(ollama_task.get), timeout=120
        )
    except asyncio.TimeoutError:
        return {"error": "Ollama processing timed out"}

    # Ждем результат TTS и возвращаем URL
    tts_task = process_text_for_tts.delay(description)
    logger.info(f"TTS task {tts_task.id} started")

    try:
        audio_url = await asyncio.wait_for(
            asyncio.to_thread(tts_task.get), timeout=120
        )
        if not audio_url or not isinstance(audio_url, str):
            logger.error(f"Invalid audio_url: {audio_url}")
            return {"error": "TTS returned invalid URL"}
        logger.info(f"TTS result: {audio_url}")
        return {"audio_url": audio_url}
    except asyncio.TimeoutError:
        logger.error(f"TTS task {tts_task.id} timed out")
        return {"error": "TTS processing timed out"}
    except Exception as e:
        logger.error(f"TTS task {tts_task.id} failed: {e}")
        return {"error": f"TTS processing failed: {str(e)}"}
import logging
from celery import Celery
from tts_wrapper import generate_tts
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Celery(
    "tasks",
    broker="redis://127.0.0.1:6379/0",
    backend="redis://127.0.0.1:6379/0",
    task_serializer="pickle",
    result_serializer="pickle",
    accept_content=["pickle", "json"],
)

@app.task(
    name="tasks.process_text_for_tts",
    retry_kwargs={"max_retries": 3, "countdown": 5}
)
def process_text_for_tts(text: str) -> str:
    try:
        public_url = generate_tts(text)
        if not isinstance(public_url, str):
            raise ValueError(f"Expected string URL, got {type(public_url)}: {public_url}")
        logger.info(f"TTS generated: {public_url}")
        return public_url
    except Exception as e:
        logger.error(f"TTS failed: {e}")
        raise
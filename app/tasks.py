from celery import Celery
import os
import uuid

BROKER_URL = os.getenv("BROKER_URL", "redis://redis:6379/0")
RESULT_BACKEND = os.getenv("RESULT_BACKEND", "redis://redis:6379/0")

celery_app = Celery(
    "tasks",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    task_serializer="pickle",
    result_serializer="pickle",
    accept_content=["pickle", "json"],
    task_track_started=True,
    task_time_limit=300,  # 5 минут на задачу
    task_soft_time_limit=240,  # мягкий лимит 4 минуты
)

celery_app.conf.task_queues = {
    "ollama": {"exchange": "ollama", "routing_key": "ollama"},
    "tts": {"exchange": "tts", "routing_key": "tts"},
}

@celery_app.task(
    name="tasks.process_image_with_ollama",
    queue="ollama",
    retry_kwargs={"max_retries": 3, "countdown": 5}
)
def process_image_with_ollama(image_id: str) -> str:
    # Эта функция будет переопределена в ollama_worker/tasks.py
    # Здесь оставляем заглушку для совместимости
    raise NotImplementedError("This task should be handled by ollama_worker")

@celery_app.task(
    name="tasks.process_text_for_tts",
    queue="tts",
    retry_kwargs={"max_retries": 3, "countdown": 5}
)
def process_text_for_tts(text: str) -> str:
    # Эта функция будет переопределена в tts_worker/tasks.py
    # Здесь оставляем заглушку для совместимости
    raise NotImplementedError("This task should be handled by tts_worker")
from celery import Celery
from .ollama_wrapper import describe_image

app = Celery(
    "tasks",
    broker="redis://127.0.0.1:6379/0",
    backend="redis://127.0.0.1:6379/0",
    task_serializer="pickle",
    result_serializer="pickle",
    accept_content=["pickle", "json"],
)

@app.task(
    name="tasks.process_image_with_ollama",
    retry_kwargs={"max_retries": 3, "countdown": 5}
)
def process_image_with_ollama(image_id: str):
    return describe_image(image_id)

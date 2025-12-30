@echo off
:: Настрой адрес Redis-сервера (где запущен API)
set BROKER_URL=redis://localhost:6379/0

:: Установим PYTHONPATH на текущую папку
set PYTHONPATH=%~dp0

:: Запуск Celery воркера на очередь tts
python -m celery -A tasks worker -Q tts --loglevel=info
pause

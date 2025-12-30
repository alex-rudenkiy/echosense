import json
import time
import soundfile as sf
import sherpa_onnx
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
import os
import uuid
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройки MinIO из переменных окружения
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "127.0.0.1:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "audio")

# Инициализация клиента MinIO
s3_client = boto3.client(
    "s3",
    endpoint_url=f"http://{MINIO_ENDPOINT}",
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    config=Config(signature_version="s3v4"),
)

# Политика публичного доступа
PUBLIC_READ_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {"AWS": "*"},
            "Action": ["s3:GetObject"],
            "Resource": [f"arn:aws:s3:::{MINIO_BUCKET}/*"]
        }
    ]
}

# Функция для проверки и создания бакета
def ensure_bucket_exists(bucket_name: str):
    try:
        # Проверяем, существует ли бакет
        s3_client.head_bucket(Bucket=bucket_name)
        logger.info(f"Bucket '{bucket_name}' already exists")
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            try:
                s3_client.create_bucket(Bucket=bucket_name)
                logger.info(f"Bucket '{bucket_name}' created successfully")
                s3_client.put_bucket_policy(
                    Bucket=bucket_name,
                    Policy=json.dumps(PUBLIC_READ_POLICY)
                )
            except ClientError as create_error:
                logger.error(f"Failed to create bucket '{bucket_name}': {create_error}")
                raise
        else:
            logger.error(f"Error checking bucket '{bucket_name}': {e}")
            raise

# Создаем бакет при запуске модуля
ensure_bucket_exists(MINIO_BUCKET)

def generate_tts(text: str):
    try:
        tts_config = sherpa_onnx.OfflineTtsConfig(
            model=sherpa_onnx.OfflineTtsModelConfig(
                vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                    model="sherpa_onnx\\bin\\vits-piper-ru_RU-irina-medium\\ru_RU-irina-medium.onnx",
                    lexicon="",
                    data_dir="sherpa_onnx\\bin\\vits-piper-ru_RU-irina-medium\\espeak-ng-data",
                    dict_dir="",
                    tokens="sherpa_onnx\\bin\\vits-piper-ru_RU-irina-medium\\tokens.txt",
                ),
                matcha=sherpa_onnx.OfflineTtsMatchaModelConfig(
                    acoustic_model="",
                    vocoder="",
                    lexicon="",
                    tokens="",
                    data_dir="",
                    dict_dir="",
                ),
                kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(
                    model="",
                    voices="",
                    tokens="",
                    data_dir="",
                    dict_dir="",
                    lexicon="",
                ),
                provider="cuda",
                debug=True,
                num_threads=8,
            ),
            rule_fsts='',
            max_num_sentences=10,
        )



        if not tts_config.validate():
            raise ValueError("Please check your config")

        tts = sherpa_onnx.OfflineTts(tts_config)

        start = time.time()
        audio = tts.generate(text, sid=0, speed=1.0)
        end = time.time()

        if len(audio.samples) == 0:
            print("Error in generating audios. Please read previous error messages.")
            return

        elapsed_seconds = end - start
        audio_duration = len(audio.samples) / audio.sample_rate
        real_time_factor = elapsed_seconds / audio_duration

        temp_filename = str(uuid.uuid4())+'.wav'

        sf.write(
            temp_filename,
            audio.samples,
            samplerate=audio.sample_rate,
            subtype="PCM_16",
        )

        # Загрузка в MinIO
        with open(temp_filename, "rb") as f:
            s3_client.upload_fileobj(f, MINIO_BUCKET, temp_filename, ExtraArgs={"ACL": "public-read"})
        
        # Удаление временного файла
        os.remove(temp_filename)

        # Формирование публичной ссылки
        public_url = f"/{MINIO_BUCKET}/{temp_filename}"
        
        logger.info(f"Saved to MinIO: {public_url}")
        logger.info(f"The text is '{text}'")
        logger.info(f"Elapsed seconds: {elapsed_seconds:.3f}")
        logger.info(f"Audio duration in seconds: {audio_duration:.3f}")
        logger.info(f"RTF: {elapsed_seconds:.3f}/{audio_duration:.3f} = {real_time_factor:.3f}")
        
        return public_url



    except Exception as e:
        logger.error(f"TTS generation failed: {e}")
        raise
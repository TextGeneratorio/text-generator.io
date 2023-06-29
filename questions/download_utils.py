from pathlib import Path

from google.cloud import storage
from loguru import logger

from questions.utils import log_time


def download_model(prefix, dl_dir):
    Path(dl_dir).mkdir(parents=True, exist_ok=True)

    bucket_name = "20-questions"
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=prefix)  # Get list of files
    # e.g gs ://20-questions/gpt-neo-model.tar.gz
    for blob in blobs:
        filename = Path(blob.name).name
        download_filename = dl_dir + filename
        if not Path(download_filename).exists():
            logger.info(f"downloading {blob.name} to {download_filename}")
            with log_time(f"download {blob.name}"):
                blob.download_to_filename(download_filename)

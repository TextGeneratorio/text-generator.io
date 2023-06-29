import subprocess
from time import sleep
from loguru import logger
import requests


def get_status_code(url):
    try:
        r = requests.get(url)
        return r.status_code
    except Exception as e:
        logger.error(e)
        return e

while True:
    status = get_status_code("https://api.text-generator.io/liveness_check")
    if status != 200:
        # run say error command
        print("error")

        while True:
            process = subprocess.Popen(["espeak", "-s", "120",  "error"], stdout=subprocess.PIPE)

            sleep(20)
        output, error = process.communicate()
    sleep(5 * 60) # 5 minutes

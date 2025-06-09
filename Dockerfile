# Core autocomplete model docker file,
# when running it can be acssed via /autocomplete?prefix=test

FROM nvidia/cuda:11.7.0-base-ubuntu20.04  as base
RUN apt-key adv --fetch-keys http://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/3bf863cc.pub && apt-get -y update

RUN apt-get install -y software-properties-common && add-apt-repository ppa:deadsnakes/ppa

RUN DEBIAN_FRONTEND=noninteractive TZ=Asia/Singapore apt-get -y update && apt-get install \
  -y --no-install-recommends python3.9

RUN apt-get install python3-venv python3-pip python3.9-distutils -y
RUN --mount=type=cache,target=/root/.cache/pip python3.9 -m pip install -U pip && python3 --version && pip3 --version
RUN #python3.9 -m pip install -U pip && python3 --version && pip3 --version
# disable tpu for now
#RUN python3.9 -m pip install pip install cloud-tpu-client==0.10 torch==1.11.0 https://storage.googleapis.com/tpu-pytorch/wheels/colab/torch_xla-1.11-cp37-cp37m-linux_x86_64.whl

RUN DEBIAN_FRONTEND=noninteractive TZ=Asia/Singapore apt-get -y update && apt install -y libsm6 libxext6 libxrender-dev python3.9-dev gcc autoconf python3-opencv git tesseract-ocr

WORKDIR /code

SHELL ["/bin/bash", "-c"]

# Install pip-tools and compilation dependencies
#RUN --mount=type=cache,target=/root/.cache/pip python3.9 -m pip install -U setuptools pip-tools
RUN python3.9 -m pip install -U setuptools pip-tools

FROM base AS python-deps

#RUN #apt install -y libsm6 libxext6 libxrender-dev

# Install python dependencies in /.venv
COPY questions/inference_server/model-requirements.txt inference_server/model-requirements.txt
#COPY OFA/fairseq OFA/fairseq
RUN --mount=type=cache,target=/root/.cache/pip python3.9 -m pip install --no-compile -r inference_server/model-requirements.txt
# tried to move fairseq later but it failed to build
#COPY inference_server/ofa-requirements.txt inference_server/ofa-requirements.txt
#RUN --mount=type=cache,target=/root/.cache/pip python3.9 -m pip install -r inference_server/ofa-requirements.txt
#RUN #python3.9 -m pip install -r inference_server/model-requirements.txt
#RUN python3.9 -m pip install gsutil # for cloning the model


ENV PYTHONPATH=.
## nltk download punkt
RUN python3.9 -m nltk.downloader punkt

FROM python-deps as test
COPY dev-requirements.txt dev-requirements.txt
#RUN --mount=type=cache,target=/root/.cache/pip pip install -r dev-requirements.txt
RUN pip install -r dev-requirements.txt

COPY main.py main.py
COPY questions/inference_server/inference_server.py inference_server.py
COPY sellerinfo.py sellerinfo.py
COPY static/ static/
RUN ln -s static/templates/ templates
RUN ln -s static/templates-game/ templates-game

COPY questions/ questions/
COPY OFA/ OFA/

COPY tests/ tests/

CMD ["pytest", "-v", "tests/unit"]
# Uncomment to get a shell for debugging "test" build target
#CMD ["bash"]

FROM python-deps as release

COPY appengine_config.py appengine_config.py
COPY main.py main.py
COPY sellerinfo.py sellerinfo.py
COPY static/ static/
RUN ln -s static/templates/ templates
RUN ln -s static/templates-game/ templates-game
COPY questions/ questions/
COPY OFA/ OFA/
COPY secrets/ secrets/
COPY secrets/ OFA/secrets/

ENV GOOGLE_APPLICATION_CREDENTIALS=secrets/google-credentials.json


ENV PROCESS_COUNT=1
ENV PORT=8080
ENV LOG_LEVEL=DEBUG
ENV SERVER_SOFTWARE=PRODUCTION
ENV TPU_IP_ADDRESS=10.2.2.2
# Note to user: update the lines above

ENV XRT_TPU_CONFIG="tpu_worker;0;$TPU_IP_ADDRESS:8470"
ENV XLA_USE_BF16=1

ENTRYPOINT gunicorn -k uvicorn.workers.UvicornWorker -b :$PORT questions.inference_server.inference_server:app --timeout 180000 --workers $PROCESS_COUNT

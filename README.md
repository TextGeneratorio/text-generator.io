# Text-Generator.io

![text generator brain](static%2Fimg%2Fandroid-chrome-192x192.png)

Text Generator is a system for;
* Balancing multiple models on the disk, RAM and GPU
* Serving AI APIs via swapping in AI Networks.
* Using data enrichment (OCR, crawling, image analysis to make prompt engineering easier)
* Generating speech and text.
* Understanding text and speech (speech to text with whisper).

Text generator can be used via API or self hosted.

Text generator balances multiple 7B models to generate text.

Text generator also enriches web links with text summaries.

If a prompt contains links to images they are converted to text using captioning and if necessary OCR.

Please support us!

You can support us by purchasing unlimited API use on [text-generator io](https://text-generator.io)

Also checkout our other projects: [Netwrck](https://netwrck.com/) AI Social chat character network/art generator.
Art Generator: [AIArt-Generator.art](https://AIArt-Generator.art)
AI Data Analyst: [Helix.app.nz](https://helix.app.nz)


Coming soon:

* Add support for other models and modalities like stable diffusion (done in https://github.com/netwrck/stable-diffusion-server)
* Train a classifier to first detect which model is best to use for a given piece of text.
* Add support/passthroughs to other models like ChatGPT and Palm.

### API

Text Generator is API compatible with OpenAI (but not the ChatGPT API yet)

There's also more control of text generation via the Text-generator API, this includes;

* Early stopping based on probability (fast autocomplete the next likely parts of text)
* max_sentences (generate only a set number of sentences at most)

Text generator also has routes for speech to text and speech generation.

See https://text-generator.io/docs

### Clone

```shell
cd
mkdir code
cd code
git clone 20-questions
```

### Local dev setup
Env vars:

```shell
GOOGLE_APPLICATION_CREDENTIALS=$HOME/code/20-questions/secrets/google-credentials.json;
PYTHONPATH=$HOME/code/20-questions:$HOME/code/20-questions/OFA
```

### machine setup without docker
###### install requirements

```shell
sudo apt install -y ffmpeg
sudo apt install -y tesseract-ocr
sudo apt install -y python3.9-distutils
```

```shell
pip install -r requirements.txt
pip install -r questions/inference_server/model-requirements.txt
pip install -r dev-requirements.txt
pip install -r requirements-test.txt
```

Using cuda is important to speed up inference.

```shell
python -m nltk.downloader punkt
```

### Running offline integration tests

Offline integration tests exercise functionality that does not require internet
access but may load heavy dependencies. After installing the `punkt` dataset
you can run them with:

```shell
pytest -m "integration and not internet"
```

Set up some environment variables in this file (fake ones are okay for local dev)

```shell
mv sellerinfo_faked.py sellerinfo.py
```

### Helper Makefile targets

Common development tasks are wrapped in the Makefile. Useful commands include:

```shell
make install          # install requirements using uv
make coverage         # run unit tests with coverage output
make ruff-fix         # run ruff with automatic fixes
make download-punkt   # download the punkt dataset for NLTK
```

### Models

Download models from huggingface.

```shell
huggingface-cli download HuggingFaceTB/SmolLM2-1.7B-Instruct --local-dir models/SmolLM-1.7B
wget -P models https://huggingface.co/geneing/Kokoro/resolve/f610f07c62f8baa30d4ed731530e490230e4ee83/kokoro-v0_19.pth

```

there CAN be three models placed:

models/tg a general model accessible with model=multilingual
models/tgz an instruct model accessible with model=instruct
models/tgc a chat model accessible with model=chat

model=best is configured to figure out which model to use based on the prompt being scored based on perplexity of each model.

This needs tuning for the avg and std deviation of the perplexity as each model has different ideas about how confidenti it is. Overtrained models are more confident about all text being in the dataset (tend to generate text verbatim from the dataset).

This model based choosing is legacy now and superceeded by MoE models which are reccomended instead.

models can be pointed to using environment variables, e.g. using models from hugginface instead for testing

```
WEIGHTS_PATH_TGZ=bigscience/bloomz
WEIGHTS_PATH_TGC=decapoda-research/llama-7b-hf
WEIGHTS_PATH=bigscience/bloom
```

### Other Models

The embedding model is a smaller model.

```shell
cd models
git clone https://huggingface.co/distilbert-base-uncased
```

whisper and STT models will be loaded on demand and placed in the huggingface cache.


#### Run

run the UI
```shell
uvicorn main:app --reload --workers=1
# or
uvicorn  -k uvicorn.workers.UvicornWorker -b :3004 main:app --timeout 60000 -w 1
```

Alternatively:
```shell
SERVER_SOFTWARE=Development/dev gunicorn -k uvicorn.workers.UvicornWorker -b :3004 main:app --timeout 60000 -w 1
```


# local docker run


### Docker building

Text Generator can be ran locally without docker.

install nvidia-docker2

```shell
sudo apt-get install nvidia-docker2
```

Text Generator is built with buildx

```shell
DOCKER_BUILDKIT=1 docker buildx build . -t questions
```

```shell
sudo docker run -v $(pwd)/models:/models -p 9000:8080 questions
```


# app engine server run
The frontend API playground is available at https://text-generator.io and written for Google App Engine.

Run locally:
```
gunicorn -k uvicorn.workers.UvicornWorker -b :3030 main:app
```


# inference server run

```
 PYTHONPATH=$(pwd):$PYTHONPATH:$(pwd)/OFA gunicorn -k uvicorn.workers.UvicornWorker -b :3030 questions.inference_server.inference_server:app
```

#### inference server run no docker with web server

```shell
PYTHONPATH=$(pwd):$(pwd)/OFA GOOGLE_APPLICATION_CREDENTIALS=secrets/google-credentials.json gunicorn -k uvicorn.workers.UvicornWorker -b :9080 questions.inference_server.inference_server:app --timeout 180000 --workers 1
PYTHONPATH=$HOME/code/20-questions:$HOME/code/20-questions/OFA:$HOME/code/20-questions/OFA/fairseq GOOGLE_APPLICATION_CREDENTIALS=secrets/google-credentials.json gunicorn -k uvicorn.workers.UvicornWorker -b :9080 questions.inference_server.inference_server:app --timeout 180000 --workers 1
```
Then go to localhost:9080/docs to use the API
#### run audio server only

Just the whisper speech to text part.
This isn't required as the inference server automatically balances these requests
```shell
PYTHONPATH=$(pwd):$(pwd)/OFA GOOGLE_APPLICATION_CREDENTIALS=secrets/google-credentials.json gunicorn -k uvicorn.workers.UvicornWorker -b :9080 audio_server.audio_server:app --timeout 180000 --workers 1 
```

### Testing

```shell
GOOGLE_APPLICATION_CREDENTIALS=secrets/google-credentials.json;PYTHONPATH=$HOME/code/20-questions:$HOME/code/20-questions/OFA pytest
```

#### Docker

#### Download Self Hosted Server

##### Direct Docker Image Download

[Docker Container .tar Download](https://storage.googleapis.com/questions-346919/text-generator.tar)

##### Container download script

```
curl https://static.text-generator.io/static/resources/download_container.sh | bash
```

After downloading the container with either method, proceed to follow the [self host instructions](https://text-generator.io/self-hosting) available for [Kubernetes](https://text-generator.io/docs/kubernetes), [Docker](https://text-generator.io/docs/docker)

### Kubernetes Deployment

See https://text-generator.io/self-hosting

Ensure tested docker locally/built one

You can setup kubernetes locally with kind if doing local kubernetes development.

```shell
k delete -f kuber/prod/deployment-gpu.yaml
k apply -f kuber/prod/deployment-gpu.yaml
k get pods
```


### Debugging docker

Run a shell in docker container
```shell
docker run -i -t -u root -v $(pwd)/models:/models --entrypoint=/bin/bash questions -c /bin/bash;
```



#### new models
clone from huggingface

```
cd models
git clone https://huggingface.co/distilbert-base-uncased
```

### maintenence 

#### run a discord bot
```shell
PYTHONPATH=$(pwd):$(pwd)/OFA python questions/disbot/disbot.py
```

#### compile dependencies
use uv pip to compile the dependencies

```shell
uv pip compile questions/inference_server/model-requirements.in    --universal -o questions/inference_server/model-requirements.txt
```

```shell
uv pip sync questions/inference_server/model-requirements.txt
```


#### remember to stretch!
stretch your body every 30 mins with the say command...

```shell
watch -n 1800 'echo "stretch your body" | espeak -s 120'
```

## Logging Configuration

All modules now use the standard `logging` package. Logging is configured via
`questions.logging_config.setup_logging`. The following environment variables can
control behaviour:

* `LOG_LEVEL` – override the default log level.
* `COLOR_LOGS` – set to `0` to disable coloured output.
* `LOG_FILE` – if set, logs will also be written to this file.

`main.py` enables Google Cloud Logging automatically when running on GCP.

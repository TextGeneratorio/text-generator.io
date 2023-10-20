# Text-Generator.io

![text generator brain](static%2Fimg%2Fandroid-chrome-192x192.png)

Text Generator is a system for;
* Balancing multiple models on the disk, RAM and GPU
* Serving AI APIs via swapping in AI Networks.
* Using data enrichment (OCR, crawling, image analysis to make prompt engineering easier)
* Generating speech and text.
* Understanding text and speech (speech to text with whisper).

Text generator can be used via API or self hosted.

Note self hosting for commercial use costs $99 annually (please support us)


Text generator balances multiple 7B models to generate text.

Text generator also enriches web links with text summaries.

If a prompt contains links to images they are converted to text using captioning and if necessary OCR.

You can also support us by purchasing [NETW Tokens](https://netwrck.com/netw-token) which will be a supported currency within the app.  

Coming soon:

* Add support for other models and modalities like stable diffusion
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
```

Using cuda is important to speed up inference.

```shell
python -m nltk.downloader punkt
```

Set up some environment variables in this file (fake ones are okay for local dev)

```shell
mv sellerinfo_faked.py sellerinfo.py
```

### Models

Text Generator models are not open source yet.

[please support us to get the models](https://text-generator.io/subscribe)

Download models and place them in the models folder.

there should be three models placed:

models/tg a general model accessible with model=multilingual
models/tgz an instruct model accessible with model=instruct
models/tgc a chat model accessible with model=chat

model=best is configured to figure out which model to use based on the prompt being scored based on perplexity of each model.

This needs tuning for the avg and std deviation of the perplexity as each model has different ideas about how confidenti it is. Overtrained models are more confident about all text being in the dataset (tend to generate text verbatim from the dataset).

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

#### remember to stretch!
stretch your body every 30 mins with the say command...

```shell
watch -n 1800 'echo "stretch your body" | espeak -s 120'
```

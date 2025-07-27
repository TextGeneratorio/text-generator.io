### Owner docs

Theres more advanced docs here for owners of the project to deploy new models.


### running a local Audio/text server

```shell
cloudflared tunnel route dns textaudio api4.text-generator.io
cloudflared tunnel --url localhost:9080 --name textaudio
```


# Speed

link models to another drive can be a good idea if you have a faster SSD as swapping models is slow
sudo ln -s $HOME/code/20-questions/models/ModernBERT-base /models/ModernBERT-base


# setup tunnel

ensure cloudflared is setup to run locally

```shell
cloudflared login
cloudflared tunnel --url localhost:9080 --name textg
```


#### Setting up kubernetes
# kubernetes cluster setup

```shell

gcloud container clusters get-credentials prod-cluster \
 --region us-central1-c --project=questions-346919
```



```shell
# docker build -t us.gcr.io/questions-346919/prod-repo/prod-app:v1 .

gcloud builds submit --tag gcr.io/prod-repo/prod-app:1.0 .

```


```shell
kubectl expose deployment prod-app --name=prod-app-service --type=LoadBalancer --port 80 --target-port 8080
```
Some of this is deprecated, but it's a good reference for setting up a new cluster/deploying to it


### build docker
xla for tpus

```shell
docker buildx build . -t gcr.io/prod-repo/prod-app-xla -f Dockerfile.xla
docker push gcr.io/prod-repo/prod-app-xla
export RELEASE="release-$(git rev-parse --short HEAD)"

echo $RELEASE

# local build
docker buildx build . -t us.gcr.io/questions-346919/prod-repo/prod-app-xla:$RELEASE

# cloud build
gcloud builds submit --tag us.gcr.io/questions-346919/prod-repo/prod-app-xla:$RELEASE . --timeout 2h
# cloud build cached
gcloud builds submit --config cloudbuild.yaml  --timeout 2h --project questions-346919


gcloud auth print-access-token   --impersonate-service-account  lee-821@questions-346919.iam.gserviceaccount.com  | docker login   -u oauth2accesstoken   --password-stdin https://us.gcr.io

docker push us.gcr.io/questions-346919/prod-repo/prod-app-xla:$RELEASE


```shell
gcloud auth configure-docker \
    us.gcr.io
gcloud auth print-access-token   --impersonate-service-account  lee-821@questions-346919.iam.gserviceaccount.com  | docker login   -u oauth2accesstoken   --password-stdin https://us.gcr.io


  docker pull     us-docker.pkg.dev/google-samples/containers/gke/hello-app:1.0

  docker tag \
    us-docker.pkg.dev/google-samples/containers/gke/hello-app:1.0 \
    us.gcr.io/questions-346919/quickstart-docker-repo/quickstart-image:tag1
gcloud auth activate-service-account leepenkman@questions-346919.iam.gserviceaccount.com --key-file=${GOOGLE_APPLICATION_CREDENTIALS}

finallly actually works ===
 gcloud builds submit -t us.gcr.io/questions-346919/prod-repo/prod-app-xla:v1 .
 gcloud builds submit -t us.gcr.io/questions-346919/prod-repo/prod-app-xla . --timeout 2h
 # doesnt work
  gcloud builds submit -t us-central1-c-docker.pkg.dev/questions-346919/prod-repo/prod-app-xla:bulk . --timeout 2h
```


```shell
# create gpu node group non spot
gcloud beta container --project "questions-346919" node-pools create "pool-gpu" --cluster "prod-cluster" --zone "us-central1-c" --node-version "1.22.8-gke.202" --machine-type "custom-4-22528" --accelerator "type=nvidia-tesla-t4,count=1" --image-type "COS_CONTAINERD" --disk-type "pd-standard" --disk-size "100" --metadata disable-legacy-endpoints=true --service-account "id-0questions@questions-346919.iam.gserviceaccount.com" --num-nodes "1" --enable-autoscaling --min-nodes "0" --max-nodes "10" --enable-autoupgrade --enable-autorepair --max-surge-upgrade 1 --max-unavailable-upgrade 0 --max-pods-per-node "110"
```


#### Pulling a customer dockerfile

# install gcloud if not available
```

curl https://sdk.cloud.google.com | bash
```
Pull a customer docker file
```
gcloud auth login
gcloud auth configure-docker \
    us.gcr.io
gcloud auth print-access-token   --impersonate-service-account  lee-821@questions-346919.iam.gserviceaccount.com  | docker login   -u oauth2accesstoken   --password-stdin https://us.gcr.io

```

setup gpu nodes

```shell
kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/container-engine-accelerators/master/nvidia-driver-installer/cos/daemonset-preloaded.yaml

gcloud container clusters update prod-cluster --enable-autoprovisioning \
    --min-cpu=1 --max-cpu=10 --min-memory=1 --max-memory=32 --region us-central1-c \
    --autoprovisioning-scopes=https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring,https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/compute

```

Try old registry
the only one that works
```shell
docker buildx build . -t us.gcr.io/questions-346919/us.gcr.io/prod-app-xla:$RELEASE

gcloud auth print-access-token   --impersonate-service-account  lee-821@questions-346919.iam.gserviceaccount.com  | docker login   -u oauth2accesstoken   --password-stdin https://us.gcr.io
docker push us.gcr.io/questions-346919/us.gcr.io/prod-app-xla
```




# Docker building

build
```shell
DOCKER_BUILDKIT=1 docker buildx build . -t questions
```

```shell
sudo docker run -v $(pwd)/models:/models -p 9000:8080 questions
sudo docker run -v $(pwd)/models:/models -p 9000:8080 us.gcr.io/questions-346919/prod-repo/prod-app-xla:$RELEASE
```

### local docker build for customers
```shell
DOCKER_BUILDKIT=1 docker buildx build -f customers.Dockerfile . -t us.gcr.io/questions-346919/prod-repo/prod-customer:v1
docker tag us.gcr.io/questions-346919/prod-repo/prod-customer:v1 text-generator-customer:v1

```
### docker save for customers

```shell
sudo docker save -o text-generator.tar text-generator-customer:v1
```
### Docker push for customers

```shell
gcloud auth login
#gcloud auth activate-service-account --key-file=secrets/google-credentials.json

gcloud auth configure-docker \
    us.gcr.io --quiet
sudo docker tag text-generator-customer:v1 us.gcr.io/questions-346919/prod-repo/prod-customer:v1
gcloud auth print-access-token   --impersonate-service-account  lee-821@questions-346919.iam.gserviceaccount.com  | docker login   -u oauth2accesstoken   --password-stdin https://us.gcr.io
gcloud auth
gcloud config set account  lee-821@questions-346919.iam.gserviceaccount.com
sudo docker login -u oauth2accesstoken -p "$(gcloud auth print-access-token)" https://us.gcr.io

# needed to rename to gcr.io plain style
sudo docker tag us.gcr.io/questions-346919/prod-repo/prod-customer:v1 gcr.io/questions-346919/prod-repo/prod-customer:v1
sudo docker push gcr.io/questions-346919/prod-repo/prod-customer:v1
```


#### Customer download of container
```shell
curl https://text-generator.io/static/resources/download_container.sh | bash
```

#### sync models

#### upload model
```shell
gsutil list gs://20-questions/models/
gsutil -m rsync -r ./models gs://20-questions/models
gsutil -m rsync -r ./models/gpt-neo-1.3B-quart gs://20-questions/models/gpt-neo-1.3B-quart
```

#### Download model

```shell
gsutil -m rsync -r gs://20-questions/models/tg-7b1 ./models/tg-7b1
```

#### delete model

```shell
gsutil rm -r gs://20-questions/models/tg-7b1
```

#### upload customer tar

```shell
gsutil cp models/text-generator.tar gs://questions-346919/text-generator.tar
```

### Example Frontend Deploy to app engine

gcloud config set project YOURPROJECT
gcloud config set account YOUREMAIL

./deploy.sh

#set -eo pipefail


# if gcloud is not setup
if ! gcloud info > /dev/null 2>&1; then
  echo "gcloud is not setup, setting up gcloud"
  curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-416.0.0-linux-x86_64.tar.gz

  tar -xf google-cloud-cli-416.0.0-linux-x86.tar.gz
  ./google-cloud-sdk/install.sh
  ./google-cloud-sdk/bin/gcloud init
fi
# check if docker is working or print if we need sudo
#docker ps > /dev/null 2>&1 || echo "docker is not working without root, please run this script with sudo" && exit 1
# was not working because of pipefail
if ! docker ps > /dev/null 2>&1; then
  echo "docker is not working without root, please run this script with sudo"
  exit 1
fi

curl -O https://storage.googleapis.com/questions-346919/customer-keys.json
gcloud auth activate-service-account --key-file=customer-keys.json

current_account=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")
gcloud config set account customer@questions-346919.iam.gserviceaccount.com
gcloud auth configure-docker \
    gcr.io --quiet


sudo docker login -u oauth2accesstoken -p "$(gcloud auth print-access-token)" https://gcr.io

gcloud auth configure-docker \
    gcr.io --quiet
# impersonation is not as reliable
#gcloud auth print-access-token   --impersonate-service-account  customer@questions-346919.iam.gserviceaccount.com  | docker login   -u oauth2accesstoken   --password-stdin https://gcr.io

docker pull gcr.io/questions-346919/prod-repo/prod-customer:v1

# reset account so we dont change peoples default account if they are already using gcloud
gcloud config set account $current_account

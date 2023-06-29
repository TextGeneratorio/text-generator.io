### setup repo


```shell
gcloud beta container --project "questions-346919" clusters create "prod-cluster" --zone "us-central1-c" --no-enable-basic-auth --cluster-version "1.22.8-gke.202" --release-channel "regular" --machine-type "e2-medium" --image-type "COS_CONTAINERD" --disk-type "pd-standard" --disk-size "100" --metadata disable-legacy-endpoints=true --scopes "https://www.googleapis.com/auth/devstorage.read_only","https://www.googleapis.com/auth/logging.write","https://www.googleapis.com/auth/monitoring","https://www.googleapis.com/auth/servicecontrol","https://www.googleapis.com/auth/service.management.readonly","https://www.googleapis.com/auth/trace.append" --max-pods-per-node "110" --num-nodes "3" --logging=SYSTEM,WORKLOAD --monitoring=SYSTEM --enable-ip-alias --network "projects/questions-346919/global/networks/default" --subnetwork "projects/questions-346919/regions/us-central1/subnetworks/default" --no-enable-intra-node-visibility --default-max-pods-per-node "110" --no-enable-master-authorized-networks --addons HorizontalPodAutoscaling,HttpLoadBalancing,GcePersistentDiskCsiDriver --enable-autoupgrade --enable-autorepair --max-surge-upgrade 1 --max-unavailable-upgrade 0 --enable-shielded-nodes --node-locations "us-central1-c" --scopes=cloud-platform \
  --enable-ip-alias \
  --enable-tpu


gcloud artifacts repositories create prod-repo \
   --repository-format=docker \
   --location=us-central1 \
   --description="Docker repository"
   
$ gcloud artifacts repositories list

                                                         ARTIFACT_REGISTRY
REPOSITORY  FORMAT  DESCRIPTION        LOCATION     LABELS  ENCRYPTION          CREATE_TIME          UPDATE_TIME          SIZE (MB)
prod-repo   DOCKER  Docker repository  us-central1          Google-managed key  2022-06-27T12:03:04  2022-06-27T12:03:04  0



POST https://container.googleapis.com/v1beta1/projects/questions-346919/locations/us-central1-c/clusters/prod-cluster/nodePools
{
  "nodePool": {
    "name": "gpu-pool",
    "config": {
      "machineType": "e2-medium",
      "diskSizeGb": 100,
      "oauthScopes": [
        "https://www.googleapis.com/auth/devstorage.read_only",
        "https://www.googleapis.com/auth/logging.write",
        "https://www.googleapis.com/auth/monitoring",
        "https://www.googleapis.com/auth/servicecontrol",
        "https://www.googleapis.com/auth/service.management.readonly",
        "https://www.googleapis.com/auth/trace.append"
      ],
      "metadata": {
        "disable-legacy-endpoints": "true"
      },
      "imageType": "COS_CONTAINERD",
      "diskType": "pd-standard",
      "shieldedInstanceConfig": {
        "enableIntegrityMonitoring": true
      }
    },
    "initialNodeCount": 1,
    "autoscaling": {
      "enabled": true,
      "maxNodeCount": 10
    },
    "management": {
      "autoUpgrade": true,
      "autoRepair": true
    },
    "maxPodsConstraint": {
      "maxPodsPerNode": "110"
    },
    "networkConfig": {},
    "version": "1.22.8-gke.202",
    "upgradeSettings": {
      "maxSurge": 1
    }
  }
}



gcloud beta container --project "questions-346919" node-pools create "gpu-pool" --cluster "prod-cluster" --zone "us-central1-c" --node-version "1.22.8-gke.202" --machine-type "n1-highmem-4" --accelerator "type=nvidia-tesla-t4,count=1" --image-type "COS_CONTAINERD" --disk-type "pd-standard" --disk-size "100" --node-labels app=prod --metadata disable-legacy-endpoints=true --scopes "https://www.googleapis.com/auth/cloud-platform" --spot --num-nodes "1" --enable-autoscaling --min-nodes "0" --max-nodes "10" --enable-autoupgrade --enable-autorepair --max-surge-upgrade 1 --max-unavailable-upgrade 0 --max-pods-per-node "108"
most recent
gcloud beta container --project "questions-346919" node-pools create "gpu-pool" --cluster "prod-cluster" --zone "us-central1-c" --node-version "1.22.8-gke.202" --machine-type "n1-highmem-4" --accelerator "type=nvidia-tesla-t4,count=1" --image-type "UBUNTU_CONTAINERD" --disk-type "pd-ssd" --disk-size "100" --metadata disable-legacy-endpoints=true --service-account "lee-821@questions-346919.iam.gserviceaccount.com" --num-nodes "1" --enable-autoscaling --min-nodes "0" --max-nodes "10" --enable-autoupgrade --enable-autorepair --max-surge-upgrade 1 --max-unavailable-upgrade 0 --max-pods-per-node "110"
```

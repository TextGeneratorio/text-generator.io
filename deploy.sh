#set -e
#set -x
#set -o pipefail

# Set the project ID
#PROJECT_ID="questions-346919"

# Use the specified project
#gcloud config set project $PROJECT_ID

# Verify the current project
#echo "Current project set to: $(gcloud config get-value project)"

# validate we can install requirements
# uv pip install -r requirements.txt
echo "WARNING: Run tests+pip install before deploying"

# Sync static files to Cloudflare R2 bucket
aws s3 sync ./static s3://text-generatorstatic/static --endpoint-url https://f76d25b8b86cfa5638f43016510d8f77.r2.cloudflarestorage.com

#gcloud app deploy --project questions-346919




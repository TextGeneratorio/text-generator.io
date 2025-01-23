#set -e
#set -x
#set -o pipefail

# Set the project ID
PROJECT_ID="questions-346919"

# Use the specified project
gcloud config set project $PROJECT_ID

# Verify the current project
echo "Current project set to: $(gcloud config get-value project)"

# validate we can install requirements
# uv pip install -r requirements.txt
echo "WARNING: Run tests+pip install before deploying"
gsutil -m rsync -r ./static gs://static.text-generator.io/static
gcloud app deploy --project questions-346919




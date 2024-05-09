# validate we can install requirements
pip install -r requirements.txt
echo "WARNING: Run tests before deploying"
gsutil -m rsync -r ./static gs://static.text-generator.io/static
gcloud app deploy --project questions-346919


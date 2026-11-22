# Deploy the UpShift backend to Cloud Run

This setup uses the same Firebase project as the Android build. It needs an
existing Firestore database and Firebase Authentication, a billing-enabled
Google Cloud project, a private Cloud Storage bucket, and a Docker repository in
Artifact Registry. Run the build and deploy from the branch containing the
schema-2 integration, live vacancy ranking, and deployment files.

## Service identity and model files

Use a dedicated Cloud Run runtime service account on the Firebase project. It
needs Firebase Authentication Viewer (`roles/firebaseauth.viewer`) for token
revocation checks and Cloud Datastore User (`roles/datastore.user`) for the
backend's Firestore reads and writes. Give it Storage Object Viewer
(`roles/storage.objectViewer`) on the model bucket. Cloud Run supplies
application default credentials through the attached service account.

After confirming that the handoff artefacts may be hosted in the project,
upload the complete `artifacts/` directory from the trusted Member 2 handoff
under a new prefix such as `schema2-v1` in the private bucket. The bundle,
deployment config, and entire encoder directory must remain together. The
Cloud Run revision mounts the bucket read-only. Use a new prefix for each model
release so earlier revisions retain their own files.

## Build and deploy

In Bash or Google Cloud Shell, replace the configuration values. The build uses
a source archive limited to the committed backend files. The model bundle and
Firebase keys stay outside the build and source repository.

```bash
PROJECT_ID='your-firebase-project-id'
REGION='your-cloud-run-region'
REPOSITORY='your-artifact-registry-repository'
MODEL_BUCKET='your-private-model-bucket'
MODEL_PREFIX='schema2-v1'
HANDOFF_ARTIFACTS='/path/to/extracted-handoff/artifacts'
RUNTIME_ACCOUNT='your-runtime-account@your-firebase-project-id.iam.gserviceaccount.com'
SERVICE='upshift-api'
REVISION=$(git rev-parse --short HEAD)
IMAGE="$REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/upshift-api:$REVISION"

gcloud storage rsync --recursive "$HANDOFF_ARTIFACTS" "gs://$MODEL_BUCKET/$MODEL_PREFIX"

git archive --format=tar.gz --output=upshift-build.tgz HEAD Dockerfile .dockerignore backend upshift_ai
gcloud builds submit upshift-build.tgz --project="$PROJECT_ID" --tag="$IMAGE"

gcloud run deploy "$SERVICE" --project="$PROJECT_ID" --region="$REGION" \
  --image="$IMAGE" --service-account="$RUNTIME_ACCOUNT" \
  --execution-environment=gen2 --port=8080 --memory=2Gi --cpu=2 \
  --timeout=120s --concurrency=2 --max-instances=2 --min-instances=0 \
  --ingress=all --no-invoker-iam-check \
  --set-env-vars="UPSHIFT_FIREBASE_PROJECT_ID=$PROJECT_ID,UPSHIFT_MODEL_PATH=/models/$MODEL_PREFIX/upshift_bundle.joblib" \
  --add-volume="name=models,type=cloud-storage,bucket=$MODEL_BUCKET,readonly=true,mount-options=uid=10001;gid=10001" \
  --add-volume-mount="volume=models,mount-path=/models"

gcloud run services describe "$SERVICE" --project="$PROJECT_ID" \
  --region="$REGION" --format='value(status.url)'
```

The Cloud Run address is reachable by the Android client. Firebase ID tokens
authenticate requests inside the API. Operator routes also require the existing
`upshift_admin` Firebase custom claim. The unauthenticated health endpoint
reports readiness only. During setup, use the existing [vacancy guide](VACANCY_BACKEND.md)
for moderation and Firestore rules. The container refuses to start if Firebase
project configuration or the selected model is missing.

## Verify and hand off to Member 3

Publish a test vacancy via the moderation API in the intended test project.
Run the smoke check with a test search that should match it. Paste a Firebase
ID token from a signed-in test account when prompted. The check validates model
readiness, rejection of unauthenticated requests, live catalogue selection, and
the expected job in the top five.

```bash
python scripts/check_backend.py 'https://your-upshift-service.run.app' \
  --search-text 'Python software development internship' \
  --expect-job-id 'your-published-vacancy-id'
```

Give Member 3 the verified HTTPS base URL and the [API contract](BACKEND_API.md).
Android sends the signed-in user's Firebase ID token as the Bearer token and
posts a JSON body such as `{"resume_text":"Python developer","top_k":5}` to
`/recommendations`. Render an empty state when the response is
`{"status":"no_match","matches":[]}` with its usual metadata. The application
can present an Apply link when `ready_for_live_application` is true.

## Google Cloud references

- [Cloud Run deployment flags](https://docs.cloud.google.com/sdk/gcloud/reference/run/deploy)
- [Private Cloud Storage volumes](https://docs.cloud.google.com/run/docs/configuring/services/cloud-storage-volume-mounts)
- [Firebase Authentication IAM roles](https://docs.cloud.google.com/iam/docs/roles-permissions/firebaseauth)
- [Firestore IAM roles](https://docs.cloud.google.com/iam/docs/roles-permissions/firestore)

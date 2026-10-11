# Deploy the backend to Google Cloud Run

This guide records how the InsightAI FastAPI backend was deployed from `Backend/` to Cloud Run.

## Deployment details

- Google Cloud project: `api-newsletter-research`
- Region: `asia-south1`
- Cloud Run service: `insightai-api`
- Runtime service account: `insightai-runtime@api-newsletter-research.iam.gserviceaccount.com`
- Public API URL: <https://insightai-api-6q72nob3na-el.a.run.app>
- Gemini API key: Secret Manager secret `gemini-api-key`
- Allowed browser origin: `https://my-newsletter.web.app`

The service was verified by requesting `/` and `/docs`; both returned HTTP 200.

## Prerequisites

Install the Google Cloud CLI, sign in, and select the project. From PowerShell:

```powershell
gcloud auth login
gcloud config set project api-newsletter-research
```

Enable the services used for Cloud Run, source builds, Artifact Registry, and Secret Manager:

```powershell
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com --project api-newsletter-research
```

## Store the Gemini key

Create a Secret Manager secret and add the Gemini key as a version. Do not put the key in a deployment command, source file, or Docker image.

```powershell
gcloud secrets create gemini-api-key --replication-policy=automatic --project api-newsletter-research
```

Add the key through **Google Cloud Console > Security > Secret Manager > `gemini-api-key` > Add new version**. If the secret already exists, add a new version rather than creating it again.

Create a dedicated runtime identity and grant it access to only this secret. If the service account already exists, skip its creation command:

```powershell
gcloud iam service-accounts create insightai-runtime --display-name="InsightAI Cloud Run runtime" --project api-newsletter-research

gcloud secrets add-iam-policy-binding gemini-api-key `
  --member="serviceAccount:insightai-runtime@api-newsletter-research.iam.gserviceaccount.com" `
  --role="roles/secretmanager.secretAccessor" `
  --project api-newsletter-research
```

## Protect local files from source upload

The source deploy uses [`.gcloudignore`](.gcloudignore) to exclude `.env`, local virtual environments, and the local Chroma database. Keep secrets in Secret Manager and do not remove these exclusions.

## Build and deploy

Cloud Run builds the Dockerfile in `Backend/`. The image starts Uvicorn on the port provided by Cloud Run. Deploy with the runtime key injected from Secret Manager:

```powershell
gcloud run deploy insightai-api `
  --source Backend `
  --project api-newsletter-research `
  --region asia-south1 `
  --no-invoker-iam-check `
  --port 8080 `
  --memory 2Gi `
  --cpu 2 `
  --timeout 300 `
  --concurrency 1 `
  --max 1 `
  --service-account insightai-runtime@api-newsletter-research.iam.gserviceaccount.com `
  --set-env-vars "GEMINI_MODEL=gemini-3.8-flash,ALLOWED_ORIGINS=https://my-newsletter.web.app" `
  --set-secrets "GEMINI_API_KEY=gemini-api-key:latest"
```

`--no-invoker-iam-check` makes the API callable by the browser frontend. This project blocks an IAM binding for `allUsers`, so `--allow-unauthenticated` alone cannot make the service public. Google documents disabling the invoker check as the supported option for this organization-policy case: [Cloud Run access control](https://docs.cloud.google.com/run/docs/securing/managing-access).

### Source build permissions

If the source build reports a permission error, grant the default Compute Engine service account access to the source archive bucket, build logs, and the Cloud Run source image repository. The project number below is `623941446686` for this deployment; replace it if deploying to a different project.

```powershell
$project = "api-newsletter-research"
$projectNumber = "623941446686"
$buildAccount = "serviceAccount:$projectNumber-compute@developer.gserviceaccount.com"

gcloud storage buckets add-iam-policy-binding gs://run-sources-api-newsletter-research-asia-south1 `
  --member=$buildAccount --role=roles/storage.objectViewer --project=$project

gcloud projects add-iam-policy-binding $project `
  --member=$buildAccount --role=roles/logging.logWriter

gcloud artifacts repositories add-iam-policy-binding cloud-run-source-deploy `
  --location=asia-south1 --project=$project `
  --member=$buildAccount --role=roles/artifactregistry.writer
```

The source archive bucket and Artifact Registry repository are created by the first source deployment. If those names differ in another project or region, use the names shown in that deployment's error or build output.

## Verify the deployment

Read the service URL from Cloud Run and check the root and FastAPI docs endpoints:

```powershell
$url = gcloud run services describe insightai-api `
  --project api-newsletter-research --region asia-south1 `
  --format="value(status.url)"

curl.exe -i "$url/"
curl.exe -i "$url/docs"
```

The root should return a JSON message that the API is running. `/docs` should return the FastAPI Swagger UI. To inspect recent service logs:

```powershell
gcloud run services logs read insightai-api --project api-newsletter-research --region asia-south1 --limit 50
```

## Point the frontend at Cloud Run

[`articleReader.tsx`](../frontend/src/components/Common/articleReader.tsx) uses `REACT_APP_API_BASE_URL` when set. The current production fallback is the Cloud Run URL above. If the build environment still sets the old Railway URL, replace it with:

```text
REACT_APP_API_BASE_URL=https://insightai-api-6q72nob3na-el.a.run.app
```

Because this is a frontend build variable, rebuild and redeploy the frontend after changing it. The backend CORS allowlist must include the frontend's exact origin; the current deployed value is `https://my-newsletter.web.app`.

## Operational notes

- Cloud Run's local filesystem is temporary. The local Chroma database under `data/chroma` is excluded from deployment and is not durable across instances or restarts. Use a managed vector database or other persistent storage if indexed articles must survive restarts.
- The service was configured with one maximum instance and concurrency one. Revisit these limits and memory/CPU settings before increasing production traffic.
- The deployed image includes `sentence-transformers` and PyTorch, so its initial build and image import can take several minutes.
- To publish a later backend change, run the same `gcloud run deploy` command from the repository root. Cloud Run creates a new revision and shifts traffic when it becomes ready.

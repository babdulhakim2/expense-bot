# ExpenseBot Server

Backend service for ExpenseBot, handling WhatsApp interactions and AI processing. Deployed on Google Cloud Run.

## Setup

1. **Environment Variables**
   Create `.env` for local development:

   ```env
   # AI/ML
   GOOGLE_GENERATIVE_AI_API_KEY=your_gemini_api_key

   # Google Cloud
   PROJECT_ID=your_project_id

   # Firebase Admin
   FIREBASE_SERVICE_ACCOUNT_KEY=your_firebase_admin_key_json

   # Development
   ENVIRONMENT=development
   USE_FIREBASE_EMULATOR=true
   FIREBASE_EMULATOR_HOST=localhost:8080
   ```

2. **Google Cloud Setup**

   ```bash
   # Install Google Cloud SDK
   curl https://sdk.cloud.google.com | bash

   # Login
   gcloud auth login

   # Set project
   gcloud config set project your-project-id

   # Enable required APIs
   gcloud services enable \
     iam.googleapis.com \
     cloudbuild.googleapis.com \
     secretmanager.googleapis.com \
     run.googleapis.com \
     artifactregistry.googleapis.com
   ```

## Cloud Run Deployment

1. **Create Artifact Registry Repository**

   ```bash
   gcloud artifacts repositories create backend \
       --repository-format=docker \
       --location=us-central1 \
       --project=your-project-id
   ```

2. **Set up Secret Manager**

   ```bash
   # Create a secret for environment variables
   gcloud secrets create expense-bot-production-secrets \
       --project=your-project-id

   # Add a new version with your .env file contents
   gcloud secrets versions add expense-bot-production-secrets \
       --data-file=.env \
       --project=your-project-id
   ```

3. **Set up Cloud Build Permissions**

   First, identify your Cloud Build service account. It follows the format:
   `PROJECT_NUMBER@cloudbuild.gserviceaccount.com`

   ```bash
   # Get your project number
   PROJECT_NUMBER=$(gcloud projects describe your-project-id \
       --format='value(projectNumber)')

   # Grant Secret Manager access
   gcloud projects add-iam-policy-binding your-project-id \
       --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
       --role="roles/secretmanager.secretAccessor"

   gcloud projects add-iam-policy-binding your-project-id \
       --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
       --role="roles/secretmanager.secretVersionAccessor"

   # Grant Cloud Run deployer permissions
   gcloud projects add-iam-policy-binding your-project-id \
       --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
       --role="roles/run.developer"

   # Grant Artifact Registry permissions
   gcloud projects add-iam-policy-binding your-project-id \
       --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
       --role="roles/artifactregistry.writer"
   ```

4. **Deploy using Cloud Build**
   ```bash
   # From src/server directory
   gcloud builds submit --config=cloudbuild-run.yaml
   ```

### Troubleshooting Deployment

Common issues and solutions:

1. **Secret Access Issues**

   - Verify secret exists: `gcloud secrets list`
   - Check secret versions: `gcloud secrets versions list expense-bot-production-secrets`
   - Verify permissions: `gcloud secrets get-iam-policy expense-bot-production-secrets`

2. **Artifact Registry Issues**

   - Ensure repository exists: `gcloud artifacts repositories list`
   - Verify permissions: `gcloud artifacts repositories get-iam-policy backend`

3. **Cloud Build Issues**
   - View build logs: `gcloud builds log [BUILD_ID]`
   - Check service account permissions:
     ```bash
     gcloud projects get-iam-policy your-project-id \
         --filter="bindings.members:cloudbuild.gserviceaccount.com" \
         --flatten="bindings[].members" \
         --format="table(bindings.role)"
     ```

## API Endpoints

- **POST** `/whatsapp`
  - Handles WhatsApp messages
  - Processes images and text
  - Returns transaction details

## Testing

```bash
# Run tests
python -m pytest

# Test with emulators
firebase emulators:start
python -m pytest tests/
```

## VLLM Inference Server Deployment

Deploy a high-performance Gemma 2B inference server using VLLM and Cloud Build.

1. **Prerequisites**

   ```bash
   # Enable required APIs
   gcloud services enable \
     artifactregistry.googleapis.com \
     cloudbuild.googleapis.com

   # Create Artifact Registry repository
   gcloud artifacts repositories create vllm-gemma-2b-it-repo \
     --repository-format=docker \
     --location=us-central1
   ```

2. **Configuration**

   - Ensure you have:
     - Hugging Face API token for model access
     - Cloud Build service account with required permissions
     - Artifact Registry repository

3. **Build and Deploy**

   ```bash
   # From src/server directory
   gcloud builds submit \
     --config cloudbuild.yaml \
     --substitutions=_HF_TOKEN="$(gcloud secrets versions access latest --secret=HF_TOKEN)"
   ```

4. **Cloud Build Configuration**
   First, create a secret for your Hugging Face token:

   ```bash
   # Create a secret for HF token
   echo -n "your_huggingface_token" | gcloud secrets create HF_TOKEN --data-file=-

   # Grant Cloud Build access to the secret
   gcloud secrets add-iam-policy-binding HF_TOKEN \
     --member="serviceAccount:YOUR_PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
     --role="roles/secretmanager.secretAccessor"
   ```

5. **Accessing the Inference Server**
   - Endpoint: `https://paligema.expensebot.xyz/v1/predict`
   - Example request:
   ```python
   response = requests.post(
       "https://paligema.expensebot.xyz/v1/predict",
       headers={"Authorization": f"Bearer {api_key}"},
       json={
           "prompt": your_prompt,
           "temperature": 0.1,
           "response_format": "json"
       }
   )
   ```

## Directory Structure

```
src/server/
├── app.py              # Main application file
├── Dockerfile          # Container configuration
├── cloudbuild-run.yaml # Cloud Build configuration
├── .env.example        # Example environment variables
└── requirements.txt    # Python dependencies
```

## Common Issues and Solutions

1. **Permission Denied for Secrets**

   - Ensure Cloud Build service account has both secretAccessor and secretVersionAccessor roles
   - Verify secret exists and has versions
   - Check if project number in service account is correct

2. **Docker Push Failures**

   - Verify Artifact Registry repository exists
   - Ensure correct image naming format: `LOCATION-docker.pkg.dev/PROJECT_ID/REPOSITORY/IMAGE`
   - Check Cloud Build service account has artifactregistry.writer role

3. **Cloud Run Deployment Failures**
   - Verify Cloud Build service account has run.developer role
   - Check if service account has permission to access all required resources
   - Ensure region and project ID are correctly specified

## Security Considerations

- Keep `.env` file secure and never commit to version control
- Use Secret Manager for all sensitive information
- Regularly rotate API keys and credentials
- Follow principle of least privilege when granting permissions

## LLM Service Deployment

Deploy a fine-tuned Gemma model for receipt processing using VLLM and Cloud Run.

### Prerequisites

1. **Enable Required APIs**

   ```bash
   gcloud services enable \
     artifactregistry.googleapis.com \
     cloudbuild.googleapis.com \
     run.googleapis.com
   ```

2. **Set up Hugging Face Token**

   ```bash
   # Create a secret for your Hugging Face token
   echo -n "your_huggingface_token" | \
     gcloud secrets create HF_TOKEN \
     --project=expense-bot-441618

   # Grant Cloud Build access to the secret
   PROJECT_NUMBER=$(gcloud projects describe expense-bot-441618 \
     --format='value(projectNumber)')

   gcloud secrets add-iam-policy-binding HF_TOKEN \
     --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
     --role="roles/secretmanager.secretAccessor"
   ```

3. **Create Artifact Registry Repository** (if not already created)
   ```bash
   gcloud artifacts repositories create backend \
     --repository-format=docker \
     --location=us-central1 \
     --project=expense-bot-441618
   ```

### Deployment Steps

1. **Verify Secret Access**

   ```bash
   # List available secrets
   gcloud secrets list

   # Verify secret versions
   gcloud secrets versions list HF_TOKEN

   # Test secret access
   gcloud secrets versions access latest --secret=HF_TOKEN
   ```

2. **Deploy using Cloud Build**

   ```bash
   # From src/server directory
   gcloud builds submit --config=cloudbuild-llm.yaml
   ```

3. **Monitor Deployment**

   ```bash
   # View build logs
   gcloud builds log [BUILD_ID]

   # List Cloud Run services
   gcloud run services list

   # View service logs
   gcloud run services logs tail llm-service
   ```

### Configuration Files

- **Dockerfile.llm**: VLLM container configuration

  ```dockerfile
  # Key configurations:
  - Base image: vllm/vllm-openai:latest
  - Model: superfunguy/palligemma-receipts-Gemma2-challenge
  - Memory: 4GB
  - CPU: 2 cores
  ```

- **cloudbuild-llm.yaml**: Cloud Build and deployment configuration
  ```yaml
  # Key settings:
  - Memory: 4Gi
  - CPU: 2
  - Min instances: 0
  - Max instances: 4
  ```

### Accessing the Service

The LLM service exposes an OpenAI-compatible API endpoint:

```python
import requests

response = requests.post(
    "https://llm-service-xxxxx-uc.a.run.app/v1/completions",
    headers={
        "Content-Type": "application/json",
    },
    json={
        "model": "superfunguy/palligemma-receipts-Gemma2-challenge",
        "prompt": "Extract details from this receipt: ...",
        "max_tokens": 500,
        "temperature": 0.1
    }
)
```

### Troubleshooting

1. **Build Failures**

   - Check if BuildKit is enabled: `DOCKER_BUILDKIT=1`
   - Verify HF_TOKEN secret access
   - Check Cloud Build service account permissions

2. **Model Download Issues**

   - Verify Hugging Face token is valid
   - Ensure you have access to the model
   - Check model name and path are correct

3. **Deployment Failures**
   - Verify memory and CPU requirements
   - Check Cloud Run service account permissions
   - Monitor resource usage and adjust limits if needed

# ExpenseBot Server

Backend service for ExpenseBot, handling WhatsApp interactions and AI processing. Deployed on Google Cloud App Engine.

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
     cloudresourcemanager.googleapis.com \
     appengine.googleapis.com
   ```

3. **Local Development**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Run locally
   python app.py
   ```

## Deployment

1. **App Engine Configuration**
   Create `env_variables.yaml` (not in git):
   ```yaml
   env_variables:
     GOOGLE_GENERATIVE_AI_API_KEY: "your_key"
     PROJECT_ID: "your_project_id"
     FIREBASE_SERVICE_ACCOUNT_KEY: |
       {
         "type": "service_account",
         ...
       }
   ```

2. **Deploy**
   ```bash
   # From src/server directory
   gcloud app deploy
   
   # View logs
   gcloud app logs tail
   ```

3. **Twilio Setup**
   - Get your App Engine URL: `https://your-project.appspot.com`
   - In Twilio Console:
     1. Go to WhatsApp > Settings
     2. Set Webhook URL: `https://your-project.appspot.com/whatsapp`
     3. Set HTTP POST for incoming messages

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
     --substitutions=_HF_TOKEN="your_huggingface_token"
   ```

4. **Cloud Build Configuration**
   The `cloudbuild.yaml` configures:
   - VLLM Docker image build
   - Hugging Face model caching
   - High-performance inference settings
   ```yaml
   steps:
     - name: "gcr.io/cloud-builders/docker"
       args:
         - build
         - --build-arg
         - HF_TOKEN=${_HF_TOKEN}
         - --tag=${_IMAGE}
         - .
   
   substitutions:
     _IMAGE: "us-central1-docker.pkg.dev/${PROJECT_ID}/vllm-gemma-2b-it-repo/vllm-gemma-2b-it"
   
   options:
     machineType: "E2_HIGHCPU_32"
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
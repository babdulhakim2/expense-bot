# ExpenseBot - AI-Powered Bookkeeping Assistant

ExpenseBot is an open-source WhatsApp-based bookkeeping assistant that uses fine-tuned version of [PalliGemma](https://huggingface.co/superfunguy/palligemma-receipts-Gemma2-challenge) to automatically process and categorize your images of receipts and expenses. 

- It interacts with Google Drive API to organize accounting records, wit sheets and drive folders.
- It also automatially detect the tax code(UK only) to enable easy VAT recording for small businesses


🔗 **Demo**: [expensebot.xyz](https://expensebot.xyz)

⚠️ **CAUTION**: This is an experimental project for personal use only. Do not rely on it for official bookkeeping or tax purposes. The AI can make mistakes and the accuracy of the processing is not guaranteed.

## Features

- 📱 **WhatsApp Integration**: Simply send your receipts via WhatsApp
- 🤖 **AI-Powered Processing**: Automatic extraction and categorization of receipt information
- 📊 **Google Sheets Integration**: Automated expense tracking in organized spreadsheets
- 🔒 **Secure & Private**: End-to-end encryption for your financial data
- ⚡ **Real-time Processing**: Instant analysis and categorization of expenses
- 📁 **Google Drive Integration**: Organized storage of receipt images and data

## Tech Stack

- **Frontend**: Next.js 18+, TypeScript, Tailwind CSS
- **Backend**: Python, Flask
- **AI/ML**: Gemma 2B,  [Palli Gemma Fine-tuned](https://huggingface.co/superfunguy/palligemma-receipts-Gemma2-challenge)
- **Storage**: Google Drive, Google Sheets, Firebase Firestore
- **Authentication**: Firebase Authentication
- **Messaging**: Twilio WhatsApp API


## Fine-Tunning
The fine tunning is done with a subset(500 image eamples) of Receipt Dataset from roboflow which can be found here: [Dataset]( https://universe.roboflow.com/elh-datasets/receipt-ebx3a). And the training/val sets where labels with Google Gemeni 1.5 Pro for Image -> JSON extraction 


## Web hook and Auth Configuration

1. **Firebase Setup:**
   
   - **Create a Firebase Project:**
     - Go to [Firebase Console](https://console.firebase.google.com/) and create a new project.
   
   - **Enable Authentication:**
     - Navigate to **Authentication** > **Sign-in method**.
     - Enable **Phone** authentication.
   
   - **Set Up Firestore:**
     - Navigate to **Firestore Database**.
     - Create a new Firestore database in **Production** mode.
   
   - **Generate Service Account Key:**
     - Go to **Project Settings** > **Service Accounts**.
     - Click on **Generate new private key** and download the JSON file.
     - Copy the content of this JSON file.
   
2. **Environment Variables:**
   
   Ensure all required environment variables are set in `.env` file or `env_variables.yaml`:
   
   ```env
   ENVIRONMENT=production
   PROJECT_ID=your-google-cloud-project-id
   
   GEMINI_MODEL=gemini-1.5-pro (Ask fallback model)
   GEMINI_TEMPERATURE=0.1
   GEMINI_TOP_P=0.95
   GEMINI_TOP_K=40
   GEMINI_MAX_OUTPUT_TOKENS=8192
   
   # DATABASE_NAME is deprecated in favor of Firestore
   
   GOOGLE_GENERATIVE_AI_API_KEY=your-google-generative-ai-api-key
   SERVICE_ACCOUNT_KEY=your-google-service-account-key  # Deprecated
   FIREBASE_SERVICE_ACCOUNT_KEY=your-firebase-service-account-key  # Added
   
   WANDB_API_KEY=your-wandb-api-key
   
   DEFAULT_USER_EMAIL=your-default-user-email
   MY_EMAIL=your-email-for-folder-sharing  # Ensure this is set
   ```
   
   - **FIREBASE_SERVICE_ACCOUNT_KEY:** Paste the JSON content from the generated Firebase service account key.

3. **Firebase Configuration in Frontend:**
   
   Create a Firebase configuration file for the frontend:
      ````javascript
   // src/config/firebaseConfig.ts
   export const firebaseConfig = {
     apiKey: "YOUR_API_KEY",
     authDomain: "YOUR_PROJECT_ID.firebaseapp.com",
     projectId: "YOUR_PROJECT_ID",
     storageBucket: "YOUR_PROJECT_ID.appspot.com",
     messagingSenderId: "YOUR_SENDER_ID",
     appId: "YOUR_APP_ID"
   };   ````
   
   - Replace the placeholder values with your actual Firebase project credentials.

4. **Update Dependencies:**
   
   After modifying `package.json`, install the new dependencies:
   
   ```bash
   yarn install
   # or
   npm install
   ```

5. **Deploy with Firebase Integration:**
   
   Follow the existing deployment steps. Ensure that Firebase-related environment variables are correctly set in your deployment environment.


## Deployment

1. Install Google Cloud SDK
2. Enable required APIs:
   ```bash
   gcloud services enable iam.googleapis.com
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable cloudresourcemanager.googleapis.com
   gcloud services enable appengine.googleapis.com
   ```
3. Configure your project:
   ```bash
   gcloud config set project expense-bot-441618
   ```
4. Deploy from the `src/server` directory:
   ```bash
   cd src/server
   pip install -r requirements.txt  # Test locally first
   python -m pytest  # If you have tests
   gcloud app deploy
   ```

Note: Make sure all required environment variables are set in `env_variables.yaml`

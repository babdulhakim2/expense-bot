# ExpenseBot - AI-Powered Bookkeeping Assistant

ExpenseBot is an open-source WhatsApp-based bookkeeping assistant that automatically processes and categorizes receipts using AI. It combines fine-tuned [PaliGemma](https://huggingface.co/superfunguy/palligemma-receipts-Gemma2-challenge/tree/main) for receipt processing with Google Workspace integration for organized bookkeeping.

🔗 **Demo**: [expensebot.xyz](https://expensebot.xyz)

## How It Works

<div align="center">
  <img src="/public/app-flow1.png" alt="ExpenseBot Process Flow" width="800"/>
  <p><em>ExpenseBot's Receipt Processing Workflow</em></p>
</div>

1. **Receipt Processing**
   - Send receipts via WhatsApp
   - AI extracts key information (amount, date, items, merchant)
   - Supports multiple currencies with automatic conversion

2. **Automated Organization**
   - Creates dedicated Google Drive folders per phone number
   - Maintains organized Google Sheets for expense tracking
   - Automatically categorizes transactions
   - Handles VAT recording for UK businesses

3. **Easy Access**
   - View expenses through WhatsApp or web interface
   - Access organized spreadsheets directly
   - Track spending patterns and categories

## Tech Stack

- **Frontend**: Next.js 18+, TypeScript, Tailwind CSS
- **Backend**: Python, Flask, Twilio API
- **AI/ML**: 
  - Gemma 2B (VLLM inference server)
  - [PaliGemma Fine-tuned](https://huggingface.co/superfunguy/palligemma-receipts-Gemma2-challenge/tree/main)
- **Infrastructure**: 
  - Firebase (Auth, Firestore)
  - Google Cloud (App Engine, Cloud Build)
  - Google Drive API (Drive, Sheets)
  - Whatsapp and Twilio API for bot interaction

## Project Structure

```
expensebot/
├── src/
│   ├── components/     # Frontend React components
│   ├── lib/           # Shared utilities
│   └── server/        # Python backend (see server/README.md)
```

## Development Setup

1. **Frontend Setup**
   ```bash
   # Install dependencies
   bun install

   # Start development server
   bun run dev
   ```

2. **Environment Variables**
   Create `.env.local` by copying `.env.example` and replacing the values with your own Firebase configuration.

3. **Backend Setup**
   See [Server README](src/server/README.md) for:
   - WhatsApp webhook setup
   - AI model deployment
   - Google Workspace integration

4. **Required Tokens**
   - Firebase configuration (see Environment Variables section)
   - [Hugging Face Access Token](https://huggingface.co/settings/tokens) for model access
   - Google Cloud project credentials

## AI Model Training

The receipt processing model was fine-tuned on:
- Dataset: Sub-set of [Receipt Dataset](https://universe.roboflow.com/elh-datasets/receipt-ebx3a) (500 examples)
- Labels: Generated using Google Gemini 1.5 Pro
- Format: Image → JSON extraction

## Deployment

1. **Frontend**: Firebase Hosting
   ```bash
   bun run build
   vercel deploy
   ```

2. **Backend**: See [Server Deployment](src/server/README.md#deployment)
   - App Engine for webhook
   - Cloud Build for AI inference



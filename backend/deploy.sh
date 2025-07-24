#!/bin/bash

# Exit on any error
set -e

# Print commands before executing
set -x

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting deployment process...${NC}"

# Ensure we're in the correct directory (server directory)
cd "$(dirname "$0")"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Check if user is logged in to gcloud
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo "Error: Not logged in to gcloud. Please run 'gcloud auth login' first."
    exit 1
fi

# Submit the build to Cloud Build
echo -e "${YELLOW}Submitting build to Cloud Build...${NC}"
gcloud builds submit --config=cloudbuild-run.yaml .

echo -e "${GREEN}Deployment completed successfully!${NC}"

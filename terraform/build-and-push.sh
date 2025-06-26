#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="${PROJECT_NAME:-easy-video-share}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
AWS_REGION="${AWS_REGION:-us-east-1}"

echo -e "${GREEN}=== AI Video Processor Docker Build & Push ===${NC}"

# Check if terraform outputs are available
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}Error: Terraform is not installed${NC}"
    exit 1
fi

# Get ECR repository URL from terraform output
echo -e "${YELLOW}Getting ECR repository URL...${NC}"
ECR_REPO=$(terraform output -raw ecr_repository_url 2>/dev/null || echo "")

if [ -z "$ECR_REPO" ]; then
    echo -e "${RED}Error: Could not get ECR repository URL from terraform output${NC}"
    echo "Please ensure you have deployed the infrastructure first:"
    echo "  terraform plan"
    echo "  terraform apply"
    exit 1
fi

echo -e "${GREEN}ECR Repository: ${ECR_REPO}${NC}"

# Extract account ID and region from ECR URL
ACCOUNT_ID=$(echo $ECR_REPO | cut -d'.' -f1)
REGION=$(echo $ECR_REPO | cut -d'.' -f4)

echo -e "${YELLOW}Logging into ECR...${NC}"
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REPO

# Build the Docker image
echo -e "${YELLOW}Building Docker image...${NC}"
cd "${SCRIPT_DIR}/video-processor"

# Build with proper tags
IMAGE_TAG="latest"
docker build -t ${PROJECT_NAME}-video-processor:${IMAGE_TAG} .
docker tag ${PROJECT_NAME}-video-processor:${IMAGE_TAG} ${ECR_REPO}:${IMAGE_TAG}

# Also tag with timestamp for versioning
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
docker tag ${PROJECT_NAME}-video-processor:${IMAGE_TAG} ${ECR_REPO}:${TIMESTAMP}

echo -e "${YELLOW}Pushing images to ECR...${NC}"
docker push ${ECR_REPO}:${IMAGE_TAG}
docker push ${ECR_REPO}:${TIMESTAMP}

echo -e "${GREEN}✅ Successfully built and pushed Docker images:${NC}"
echo -e "  📦 ${ECR_REPO}:${IMAGE_TAG}"
echo -e "  📦 ${ECR_REPO}:${TIMESTAMP}"

echo -e "${GREEN}=== Build Complete ===${NC}"
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Update your ECS task definition to use the new image"
echo "2. Deploy your ECS service"
echo "3. Test the video processing endpoint"

# Output image URI for easy copying
echo -e "${GREEN}Image URI for ECS Task Definition:${NC}"
echo "${ECR_REPO}:${IMAGE_TAG}" 
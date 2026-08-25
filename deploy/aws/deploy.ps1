# Build, push, and deploy TAGS Agency OS to AWS App Runner (scale-to-zero).
#
# Prereqs (one-time):
#   1) Install Docker Desktop (https://www.docker.com/products/docker-desktop)
#   2) aws configure  (Access Key / Secret for account 176980002493, region us-east-1)
#   3) Deploy the IaC once:
#        aws cloudformation deploy --template-file deploy/aws/apprunner.yaml `
#            --stack-name tags-agency-os --capabilities CAPABILITY_IAM
#
# Then run this script to build + push the image; App Runner auto-serves it.

$ErrorActionPreference = "Stop"
$Region   = "us-east-1"
$Account  = (aws sts get-caller-identity --query Account --output text)
$RepoName = "tags-agency-os"
$Tag      = "latest"
$EcrUri   = "$Account.dkr.ecr.$Region.amazonaws.com/$RepoName`:$Tag"

Write-Host "==> Logging in to ECR"
aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin "$Account.dkr.ecr.$Region.amazonaws.com"

Write-Host "==> Building image $EcrUri"
docker build -t $EcrUri -f Dockerfile .

Write-Host "==> Pushing image"
docker push $EcrUri

Write-Host "==> Done. App Runner will pick up $EcrUri (scale-to-zero, $0 idle)."
Write-Host "    Get the URL: aws cloudformation describe-stacks --stack-name tags-agency-os --query 'Stacks[0].Outputs'"

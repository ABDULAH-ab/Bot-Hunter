#!/bin/bash
# BotHunter Frontend Deploy Script
# Usage: ./deploy-frontend.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/Web/frontend"
S3_BUCKET="s3://bothunter-frontend-app"
CF_DISTRIBUTION="E39U3C8X30P3K0"

echo "🔨 Building frontend..."
cd "$FRONTEND_DIR"
npm run build 2>&1 | tail -5

echo ""
echo "📤 Uploading to S3..."
aws s3 sync build/ "$S3_BUCKET" --delete | tail -5

echo ""
echo "🔄 Invalidating CloudFront cache..."
INVALIDATION_ID=$(aws cloudfront create-invalidation \
  --distribution-id "$CF_DISTRIBUTION" \
  --paths "/*" \
  --query 'Invalidation.Id' --output text)
echo "   Invalidation: $INVALIDATION_ID"

echo ""
echo "✅ Frontend deployed to https://bothunter.app"
echo "   Cache invalidation in progress (~1-2 min)"

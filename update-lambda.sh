#!/bin/bash

# Update Lambda Function with Hybrid Model (SageMaker + Rule-Based Fallback)
# This script deploys the updated Lambda function code

echo "🚀 Updating Lambda function with hybrid model architecture..."

# Create deployment package
echo "📦 Creating deployment package..."
zip -r lambda-deployment.zip lambda_function.py

# Update Lambda function
echo "⬆️  Uploading to AWS Lambda..."
aws lambda update-function-code \
  --function-name return-abuse-risk-scorer \
  --zip-file fileb://lambda-deployment.zip \
  --region ap-south-1

# Check if successful
if [ $? -eq 0 ]; then
    echo "✅ Lambda function updated successfully!"
    echo "🤖 Now using hybrid model architecture:"
    echo "   • Primary: SageMaker ML (if endpoint exists)"
    echo "   • Fallback: Rule-based algorithm (always works)"
    echo "   • Explanations: Amazon Bedrock Claude Sonnet 4"
    echo ""
    echo "Current status: Using rule-based (SageMaker not deployed yet)"
    echo ""
    echo "Next steps:"
    echo "1. Test your API: https://nglukkm7m9.execute-api.ap-south-1.amazonaws.com/prod/risk-score"
    echo "2. (Optional) Deploy SageMaker: ./deploy-sagemaker-optional.sh"
    echo "3. Focus on PowerPoint presentation!"
else
    echo "❌ Failed to update Lambda function"
    exit 1
fi

# Clean up
rm lambda-deployment.zip
echo "🧹 Cleaned up deployment package"

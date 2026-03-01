#!/bin/bash

# Optional SageMaker Deployment
# This script deploys a SageMaker endpoint for ML-based predictions
# If not deployed, the system will use rule-based fallback

echo "🤖 SageMaker ML Model Deployment (Optional)"
echo "============================================"
echo ""
echo "⚠️  IMPORTANT: This is OPTIONAL for hackathon submission"
echo "Your system already works with rule-based predictions!"
echo ""
echo "SageMaker deployment will:"
echo "  • Cost ~$50-100 for training + endpoint"
echo "  • Take 60-90 minutes to complete"
echo "  • Require real training data (not just synthetic)"
echo ""
echo "Benefits:"
echo "  • ML-based predictions (potentially more accurate)"
echo "  • Shows advanced AWS service usage"
echo "  • Automatic fallback to rules if endpoint fails"
echo ""

read -p "Do you want to proceed with SageMaker deployment? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ SageMaker deployment cancelled"
    echo "✅ Your system will continue using rule-based predictions"
    exit 0
fi

echo ""
echo "📊 Step 1: Generating training data..."
cd sample-data
python3 generate_realistic_india_data.py

if [ $? -ne 0 ]; then
    echo "❌ Failed to generate training data"
    exit 1
fi

echo ""
echo "☁️  Step 2: Creating S3 bucket for training data..."
BUCKET_NAME="return-abuse-ml-training-$(date +%s)"
aws s3 mb s3://$BUCKET_NAME --region ap-south-1

if [ $? -ne 0 ]; then
    echo "❌ Failed to create S3 bucket"
    exit 1
fi

echo ""
echo "⬆️  Step 3: Uploading training data to S3..."
aws s3 cp returns.csv s3://$BUCKET_NAME/training-data/returns.csv
aws s3 cp customers.csv s3://$BUCKET_NAME/training-data/customers.csv
aws s3 cp orders.csv s3://$BUCKET_NAME/training-data/orders.csv

cd ..

echo ""
echo "🚀 Step 4: Starting SageMaker training job..."
cd sagemaker-training

# Update deploy script with bucket name
sed -i.bak "s/your-bucket-name/$BUCKET_NAME/g" deploy-sagemaker.py

python3 deploy-sagemaker.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SageMaker deployment initiated!"
    echo ""
    echo "📋 Next steps:"
    echo "  1. Training job will take 15-30 minutes"
    echo "  2. Endpoint deployment takes another 5-10 minutes"
    echo "  3. Monitor progress in SageMaker console:"
    echo "     https://console.aws.amazon.com/sagemaker/home?region=ap-south-1"
    echo ""
    echo "  4. Once complete, update Lambda function:"
    echo "     ./update-lambda.sh"
    echo ""
    echo "  5. Test your API - it will automatically use SageMaker!"
    echo ""
    echo "💡 If SageMaker fails, Lambda automatically falls back to rules"
else
    echo ""
    echo "❌ SageMaker deployment failed"
    echo "✅ No worries! Your system still works with rule-based predictions"
fi

cd ..

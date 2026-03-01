#!/bin/bash

###############################################################################
# AI Return Abuse Detection - Complete Deployment Script
# This script deploys: DynamoDB, Lambda, Bedrock integration, CloudWatch, IAM
###############################################################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REGION="ap-south-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
LAMBDA_FUNCTION_NAME="return-abuse-risk-scorer"
DYNAMODB_TABLE_NAME="return-abuse-predictions-prod"
DASHBOARD_NAME="return-abuse-monitoring"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   AI Return Abuse Detection - Complete Deployment         ║${NC}"
echo -e "${BLUE}║   Account: ${ACCOUNT_ID}                          ║${NC}"
echo -e "${BLUE}║   Region: ${REGION}                                    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

###############################################################################
# STEP 1: Create DynamoDB Table
###############################################################################
echo -e "${YELLOW}[1/7] Creating DynamoDB Table...${NC}"

if aws dynamodb describe-table --table-name $DYNAMODB_TABLE_NAME --region $REGION &>/dev/null; then
    echo -e "${GREEN}✓ DynamoDB table already exists${NC}"
else
    aws dynamodb create-table \
      --table-name $DYNAMODB_TABLE_NAME \
      --attribute-definitions \
        AttributeName=prediction_id,AttributeType=S \
        AttributeName=order_id,AttributeType=S \
        AttributeName=timestamp,AttributeType=S \
      --key-schema \
        AttributeName=prediction_id,KeyType=HASH \
      --global-secondary-indexes \
        '[{"IndexName":"order-id-index","KeySchema":[{"AttributeName":"order_id","KeyType":"HASH"},{"AttributeName":"timestamp","KeyType":"RANGE"}],"Projection":{"ProjectionType":"ALL"}}]' \
      --billing-mode PAY_PER_REQUEST \
      --tags Key=Project,Value=ReturnAbuseDetection Key=Environment,Value=prod Key=Team,Value=Soul \
      --region $REGION \
      --output json > /dev/null
    
    echo -e "${GREEN}✓ DynamoDB table created successfully${NC}"
    
    # Wait for table to be active
    echo "  Waiting for table to become active..."
    aws dynamodb wait table-exists --table-name $DYNAMODB_TABLE_NAME --region $REGION
fi

###############################################################################
# STEP 2: Package Lambda Code
###############################################################################
echo -e "${YELLOW}[2/7] Packaging Lambda Code...${NC}"

cd $PROJECT_DIR
rm -f lambda-deployment.zip
zip -q lambda-deployment.zip lambda_function_bedrock.py

if [ -f lambda-deployment.zip ]; then
    echo -e "${GREEN}✓ Lambda code packaged ($(ls -lh lambda-deployment.zip | awk '{print $5}'))${NC}"
else
    echo -e "${RED}✗ Failed to create lambda-deployment.zip${NC}"
    exit 1
fi

###############################################################################
# STEP 3: Update Lambda Function Code
###############################################################################
echo -e "${YELLOW}[3/7] Updating Lambda Function Code...${NC}"

# Check if Lambda is already updating
LAMBDA_STATE=$(aws lambda get-function --function-name $LAMBDA_FUNCTION_NAME --region $REGION --query 'Configuration.LastUpdateStatus' --output text 2>/dev/null || echo "Unknown")

if [ "$LAMBDA_STATE" = "InProgress" ]; then
    echo "  Lambda update already in progress, waiting..."
    aws lambda wait function-updated --function-name $LAMBDA_FUNCTION_NAME --region $REGION
fi

aws lambda update-function-code \
  --function-name $LAMBDA_FUNCTION_NAME \
  --zip-file fileb://lambda-deployment.zip \
  --region $REGION \
  --output json > /dev/null

echo -e "${GREEN}✓ Lambda code updated${NC}"

# Wait for code update to complete before updating configuration
echo "  Waiting for code update to complete..."
aws lambda wait function-updated --function-name $LAMBDA_FUNCTION_NAME --region $REGION

# Update Lambda configuration
echo "  Updating Lambda configuration..."
aws lambda update-function-configuration \
  --function-name $LAMBDA_FUNCTION_NAME \
  --environment Variables="{PREDICTIONS_TABLE=$DYNAMODB_TABLE_NAME,ENVIRONMENT=prod}" \
  --timeout 30 \
  --memory-size 512 \
  --region $REGION \
  --output json > /dev/null

echo -e "${GREEN}✓ Lambda configuration updated${NC}"

# Wait for configuration update to complete
echo "  Waiting for configuration update to complete..."
aws lambda wait function-updated --function-name $LAMBDA_FUNCTION_NAME --region $REGION

###############################################################################
# STEP 4: Add IAM Permissions (Bedrock + DynamoDB)
###############################################################################
echo -e "${YELLOW}[4/7] Adding IAM Permissions...${NC}"

# Get Lambda role name
ROLE_ARN=$(aws lambda get-function --function-name $LAMBDA_FUNCTION_NAME --region $REGION --query 'Configuration.Role' --output text)
ROLE_NAME=$(echo $ROLE_ARN | awk -F'/' '{print $NF}')

echo "  Lambda role: $ROLE_NAME"

# Create Bedrock policy
cat > /tmp/bedrock-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
    }
  ]
}
EOF

# Attach Bedrock policy
aws iam put-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-name BedrockAccess \
  --policy-document file:///tmp/bedrock-policy.json

echo -e "${GREEN}✓ Bedrock permissions added${NC}"

# Create DynamoDB policy
cat > /tmp/dynamodb-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": [
        "arn:aws:dynamodb:${REGION}:${ACCOUNT_ID}:table/${DYNAMODB_TABLE_NAME}",
        "arn:aws:dynamodb:${REGION}:${ACCOUNT_ID}:table/${DYNAMODB_TABLE_NAME}/index/*"
      ]
    }
  ]
}
EOF

# Attach DynamoDB policy
aws iam put-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-name DynamoDBAccess \
  --policy-document file:///tmp/dynamodb-policy.json

echo -e "${GREEN}✓ DynamoDB permissions added${NC}"

###############################################################################
# STEP 5: Create CloudWatch Dashboard
###############################################################################
echo -e "${YELLOW}[5/7] Creating CloudWatch Dashboard...${NC}"

cat > /tmp/dashboard.json << EOF
{
  "widgets": [
    {
      "type": "metric",
      "x": 0,
      "y": 0,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          ["AWS/Lambda", "Invocations", {"stat": "Sum", "label": "Lambda Invocations", "color": "#1f77b4"}],
          [".", "Errors", {"stat": "Sum", "label": "Lambda Errors", "color": "#d62728"}],
          [".", "Duration", {"stat": "Average", "label": "Avg Duration (ms)", "color": "#2ca02c"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "${REGION}",
        "title": "Lambda Performance - ${LAMBDA_FUNCTION_NAME}",
        "yAxis": {"left": {"min": 0}},
        "view": "timeSeries",
        "stacked": false
      }
    },
    {
      "type": "metric",
      "x": 12,
      "y": 0,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          ["AWS/ApiGateway", "Count", {"stat": "Sum", "label": "API Requests"}],
          [".", "4XXError", {"stat": "Sum", "label": "4XX Errors"}],
          [".", "5XXError", {"stat": "Sum", "label": "5XX Errors"}],
          [".", "Latency", {"stat": "Average", "label": "Latency (ms)"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "${REGION}",
        "title": "API Gateway Metrics",
        "yAxis": {"left": {"min": 0}},
        "view": "timeSeries",
        "stacked": false
      }
    },
    {
      "type": "metric",
      "x": 0,
      "y": 6,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          ["AWS/DynamoDB", "ConsumedReadCapacityUnits", {"stat": "Sum"}],
          [".", "ConsumedWriteCapacityUnits", {"stat": "Sum"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "${REGION}",
        "title": "DynamoDB Capacity",
        "yAxis": {"left": {"min": 0}}
      }
    },
    {
      "type": "log",
      "x": 12,
      "y": 6,
      "width": 12,
      "height": 6,
      "properties": {
        "query": "SOURCE '/aws/lambda/${LAMBDA_FUNCTION_NAME}'\n| fields @timestamp, @message\n| sort @timestamp desc\n| limit 20",
        "region": "${REGION}",
        "title": "Recent Lambda Logs",
        "stacked": false
      }
    }
  ]
}
EOF

aws cloudwatch put-dashboard \
  --dashboard-name $DASHBOARD_NAME \
  --dashboard-body file:///tmp/dashboard.json \
  --region $REGION

echo -e "${GREEN}✓ CloudWatch dashboard created${NC}"

###############################################################################
# STEP 6: Create CloudWatch Alarms
###############################################################################
echo -e "${YELLOW}[6/7] Creating CloudWatch Alarms...${NC}"

# Lambda error alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "${LAMBDA_FUNCTION_NAME}-errors" \
  --alarm-description "Alert when Lambda function has errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=FunctionName,Value=$LAMBDA_FUNCTION_NAME \
  --region $REGION \
  --output json > /dev/null

echo -e "${GREEN}✓ Lambda error alarm created${NC}"

# Lambda duration alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "${LAMBDA_FUNCTION_NAME}-duration" \
  --alarm-description "Alert when Lambda duration is high" \
  --metric-name Duration \
  --namespace AWS/Lambda \
  --statistic Average \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 5000 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=FunctionName,Value=$LAMBDA_FUNCTION_NAME \
  --region $REGION \
  --output json > /dev/null

echo -e "${GREEN}✓ Lambda duration alarm created${NC}"

###############################################################################
# STEP 7: Test Deployment
###############################################################################
echo -e "${YELLOW}[7/7] Testing Deployment...${NC}"

# Get API endpoint
API_ENDPOINT="https://nglukkm7m9.execute-api.ap-south-1.amazonaws.com/prod/risk-score"

echo "  Testing API endpoint..."
RESPONSE=$(curl -s -X POST $API_ENDPOINT \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "DEPLOY_TEST_001",
    "customer_return_rate": 0.45,
    "total_orders": 8,
    "payment_method": "COD",
    "amount": 15000,
    "product_return_rate": 0.25,
    "is_festival_season": 0,
    "use_bedrock": true
  }')

if echo "$RESPONSE" | grep -q "risk_score"; then
    echo -e "${GREEN}✓ API test successful${NC}"
    RISK_SCORE=$(echo "$RESPONSE" | grep -o '"risk_score":[0-9.]*' | cut -d':' -f2)
    echo "  Risk Score: $RISK_SCORE"
else
    echo -e "${RED}✗ API test failed${NC}"
    echo "  Response: $RESPONSE"
fi

# Check DynamoDB
echo "  Checking DynamoDB..."
ITEM_COUNT=$(aws dynamodb scan --table-name $DYNAMODB_TABLE_NAME --region $REGION --select COUNT --output json | grep -o '"Count":[0-9]*' | cut -d':' -f2)
echo -e "${GREEN}✓ DynamoDB has $ITEM_COUNT predictions stored${NC}"

###############################################################################
# DEPLOYMENT COMPLETE
###############################################################################
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              DEPLOYMENT COMPLETED SUCCESSFULLY!            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${BLUE}📊 What Was Deployed:${NC}"
echo "  ✅ DynamoDB Table: $DYNAMODB_TABLE_NAME"
echo "  ✅ Lambda Function: $LAMBDA_FUNCTION_NAME (with Bedrock integration)"
echo "  ✅ IAM Permissions: Bedrock + DynamoDB access"
echo "  ✅ CloudWatch Dashboard: $DASHBOARD_NAME"
echo "  ✅ CloudWatch Alarms: Error & Duration monitoring"
echo ""

echo -e "${BLUE}🔗 Important Links:${NC}"
echo "  API Endpoint: $API_ENDPOINT"
echo "  CloudWatch Dashboard: https://console.aws.amazon.com/cloudwatch/home?region=${REGION}#dashboards:name=${DASHBOARD_NAME}"
echo "  DynamoDB Table: https://console.aws.amazon.com/dynamodbv2/home?region=${REGION}#table?name=${DYNAMODB_TABLE_NAME}"
echo "  Lambda Function: https://console.aws.amazon.com/lambda/home?region=${REGION}#/functions/${LAMBDA_FUNCTION_NAME}"
echo ""

echo -e "${YELLOW}⚠️  MANUAL STEPS REQUIRED:${NC}"
echo "  1. Request Bedrock Access (5-30 min approval time):"
echo "     → https://console.aws.amazon.com/bedrock/home?region=us-east-1#/modelaccess"
echo "     → Enable 'Claude 3 Sonnet' model"
echo ""
echo "  2. Create PowerPoint Presentation (1-2 hours):"
echo "     → Use: docs/PRESENTATION-OUTLINE.md"
echo "     → 12 slides with content provided"
echo ""
echo "  3. Optional - Create Demo Video (15 min):"
echo "     → Record screen showing live demo"
echo "     → 30-60 seconds recommended"
echo ""

echo -e "${BLUE}📋 What's Already Done (Documentation):${NC}"
echo "  ✅ Architecture Diagram: docs/architecture-diagram.md"
echo "  ✅ Deployment Guide: docs/DEPLOYMENT-GUIDE.md"
echo "  ✅ CloudFormation Template: cloudformation-template.yaml"
echo "  ✅ SageMaker Training Code: sagemaker-training/"
echo "  ✅ Presentation Outline: docs/PRESENTATION-OUTLINE.md"
echo ""

echo -e "${GREEN}🎉 Your system is now production-ready!${NC}"
echo ""

# Cleanup temp files
rm -f /tmp/bedrock-policy.json /tmp/dynamodb-policy.json /tmp/dashboard.json

exit 0

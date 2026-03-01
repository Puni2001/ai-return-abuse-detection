# Deployment Guide - AI Return Abuse Detection System

## Quick Start (5 Minutes)

### Prerequisites
- AWS Account with admin access
- AWS CLI installed and configured
- Python 3.11 installed locally

### Step 1: Enable Amazon Bedrock Access

```bash
# Go to AWS Console → Amazon Bedrock → Model access
# Request access to: Claude 3 Sonnet
# Wait for approval (usually instant for Claude models)
```

### Step 2: Deploy Infrastructure

```bash
# Clone repository
git clone https://github.com/Puni2001/ai-return-abuse-detection.git
cd ai-return-abuse-detection

# Package Lambda function
zip -r lambda-deployment.zip lambda_function_bedrock.py

# Create S3 bucket for Lambda code (if needed)
aws s3 mb s3://return-abuse-lambda-code-$(aws sts get-caller-identity --query Account --output text)

# Upload Lambda code
aws s3 cp lambda-deployment.zip s3://return-abuse-lambda-code-$(aws sts get-caller-identity --query Account --output text)/

# Deploy CloudFormation stack
aws cloudformation create-stack \
  --stack-name return-abuse-prod \
  --template-body file://cloudformation-template.yaml \
  --parameters ParameterKey=Environment,ParameterValue=prod \
  --capabilities CAPABILITY_NAMED_IAM \
  --region ap-south-1

# Wait for stack creation (5-10 minutes)
aws cloudformation wait stack-create-complete \
  --stack-name return-abuse-prod \
  --region ap-south-1

# Get API endpoint
aws cloudformation describe-stacks \
  --stack-name return-abuse-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text \
  --region ap-south-1
```

### Step 3: Test the API

```bash
# Get your API endpoint from previous step
API_ENDPOINT="https://xxx.execute-api.ap-south-1.amazonaws.com/prod/risk-score"

# Test with sample request
curl -X POST $API_ENDPOINT \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "TEST001",
    "customer_return_rate": 0.35,
    "total_orders": 12,
    "payment_method": "COD",
    "amount": 8500,
    "product_return_rate": 0.22,
    "is_festival_season": 0
  }'
```

Expected Response:
```json
{
  "order_id": "TEST001",
  "risk_score": 0.65,
  "risk_level": "medium",
  "recommended_action": "otp_verification",
  "explanation": {
    "generated_by": "bedrock_claude_3_sonnet",
    "explanation_text": "This order requires additional verification due to elevated return risk patterns. The customer has a 35% return rate across 12 orders, and this is a Cash on Delivery order valued at ₹8,500. The product category also shows a 22% return rate. Recommend OTP verification before processing."
  },
  "confidence": 0.3,
  "model_version": "v1.1-bedrock-enhanced",
  "timestamp": "2026-03-01T10:30:00.000Z"
}
```

---

## Detailed Deployment Steps

### Option 1: AWS Console (Manual)

#### 1. Create DynamoDB Table

1. Go to AWS Console → DynamoDB → Create table
2. Table name: `return-abuse-predictions-prod`
3. Partition key: `prediction_id` (String)
4. Settings: On-demand capacity
5. Add Global Secondary Index:
   - Index name: `order-id-index`
   - Partition key: `order_id` (String)
   - Sort key: `timestamp` (String)
6. Enable TTL on attribute: `ttl`
7. Create table

#### 2. Create S3 Bucket

1. Go to AWS Console → S3 → Create bucket
2. Bucket name: `return-abuse-data-lake-<your-account-id>`
3. Region: ap-south-1 (Mumbai)
4. Block all public access: Enabled
5. Versioning: Enabled
6. Create bucket

#### 3. Create IAM Role for Lambda

1. Go to AWS Console → IAM → Roles → Create role
2. Trusted entity: Lambda
3. Attach policies:
   - `AWSLambdaBasicExecutionRole`
4. Add inline policy for Bedrock:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
    }
  ]
}
```
5. Add inline policy for DynamoDB:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:Query"
      ],
      "Resource": [
        "arn:aws:dynamodb:ap-south-1:*:table/return-abuse-predictions-prod",
        "arn:aws:dynamodb:ap-south-1:*:table/return-abuse-predictions-prod/index/*"
      ]
    }
  ]
}
```
6. Role name: `return-abuse-lambda-role-prod`
7. Create role

#### 4. Create Lambda Function

1. Go to AWS Console → Lambda → Create function
2. Function name: `return-abuse-risk-scorer-prod`
3. Runtime: Python 3.11
4. Architecture: x86_64
5. Execution role: Use existing role → `return-abuse-lambda-role-prod`
6. Create function
7. Upload code:
   - Copy content from `lambda_function_bedrock.py`
   - Paste in code editor
   - Deploy
8. Configuration:
   - Timeout: 30 seconds
   - Memory: 512 MB
   - Environment variables:
     - `PREDICTIONS_TABLE`: `return-abuse-predictions-prod`
     - `ENVIRONMENT`: `prod`

#### 5. Create API Gateway

1. Go to AWS Console → API Gateway → Create API
2. Choose: REST API
3. API name: `return-abuse-api-prod`
4. Create API
5. Create resource:
   - Resource name: `risk-score`
   - Resource path: `/risk-score`
6. Create method: POST
   - Integration type: Lambda Function
   - Lambda function: `return-abuse-risk-scorer-prod`
   - Use Lambda Proxy integration: Yes
7. Enable CORS:
   - Actions → Enable CORS
   - Access-Control-Allow-Origin: `*`
8. Deploy API:
   - Actions → Deploy API
   - Stage name: `prod`
9. Copy Invoke URL

### Option 2: AWS CLI (Automated)

See "Quick Start" section above.

### Option 3: CloudFormation (Recommended)

```bash
# Deploy complete stack
aws cloudformation create-stack \
  --stack-name return-abuse-prod \
  --template-body file://cloudformation-template.yaml \
  --parameters ParameterKey=Environment,ParameterValue=prod \
  --capabilities CAPABILITY_NAMED_IAM \
  --region ap-south-1
```

---

## Update Existing Lambda Function

If you already have the Lambda deployed and want to update it:

```bash
# Update Lambda code
zip -r lambda-deployment.zip lambda_function_bedrock.py

aws lambda update-function-code \
  --function-name return-abuse-risk-scorer-prod \
  --zip-file fileb://lambda-deployment.zip \
  --region ap-south-1

# Update environment variables
aws lambda update-function-configuration \
  --function-name return-abuse-risk-scorer-prod \
  --environment Variables="{PREDICTIONS_TABLE=return-abuse-predictions-prod,ENVIRONMENT=prod}" \
  --region ap-south-1
```

---

## Verify Deployment

### 1. Check Lambda Function

```bash
# Test Lambda directly
aws lambda invoke \
  --function-name return-abuse-risk-scorer-prod \
  --payload '{"order_id":"TEST001","customer_return_rate":0.35,"total_orders":12,"payment_method":"COD","amount":8500,"product_return_rate":0.22,"is_festival_season":0}' \
  --region ap-south-1 \
  response.json

cat response.json
```

### 2. Check DynamoDB

```bash
# Query predictions table
aws dynamodb scan \
  --table-name return-abuse-predictions-prod \
  --limit 5 \
  --region ap-south-1
```

### 3. Check CloudWatch Logs

```bash
# View Lambda logs
aws logs tail /aws/lambda/return-abuse-risk-scorer-prod \
  --follow \
  --region ap-south-1
```

### 4. Check API Gateway

```bash
# Test API endpoint
curl -X POST https://YOUR_API_ID.execute-api.ap-south-1.amazonaws.com/prod/risk-score \
  -H "Content-Type: application/json" \
  -d '{"order_id":"TEST001","customer_return_rate":0.15,"total_orders":25,"payment_method":"Prepaid","amount":2500,"product_return_rate":0.10,"is_festival_season":1}'
```

---

## Troubleshooting

### Issue: Bedrock Access Denied

**Error**: `AccessDeniedException: Could not access model`

**Solution**:
1. Go to AWS Console → Amazon Bedrock → Model access
2. Request access to Claude 3 Sonnet
3. Wait for approval (usually instant)
4. Verify IAM role has `bedrock:InvokeModel` permission

### Issue: Lambda Timeout

**Error**: `Task timed out after 3.00 seconds`

**Solution**:
```bash
# Increase timeout to 30 seconds
aws lambda update-function-configuration \
  --function-name return-abuse-risk-scorer-prod \
  --timeout 30 \
  --region ap-south-1
```

### Issue: DynamoDB Access Denied

**Error**: `AccessDeniedException: User is not authorized to perform: dynamodb:PutItem`

**Solution**:
1. Check IAM role attached to Lambda
2. Verify DynamoDB policy includes `PutItem`, `GetItem`, `Query`
3. Verify table name matches environment variable

### Issue: CORS Error in Browser

**Error**: `Access to fetch at '...' from origin '...' has been blocked by CORS policy`

**Solution**:
1. Go to API Gateway → Resources → /risk-score
2. Actions → Enable CORS
3. Set Access-Control-Allow-Origin to `*`
4. Deploy API again

---

## Monitoring & Maintenance

### CloudWatch Dashboard

```bash
# View CloudWatch dashboard
aws cloudwatch get-dashboard \
  --dashboard-name return-abuse-monitoring-prod \
  --region ap-south-1
```

### Set Up Alarms

```bash
# Create alarm for Lambda errors
aws cloudwatch put-metric-alarm \
  --alarm-name return-abuse-lambda-errors \
  --alarm-description "Alert when Lambda has errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=FunctionName,Value=return-abuse-risk-scorer-prod \
  --region ap-south-1
```

### View Metrics

```bash
# Lambda invocations
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=return-abuse-risk-scorer-prod \
  --start-time 2026-03-01T00:00:00Z \
  --end-time 2026-03-01T23:59:59Z \
  --period 3600 \
  --statistics Sum \
  --region ap-south-1
```

---

## Cost Management

### Set Up Billing Alerts

```bash
# Create billing alarm (in us-east-1)
aws cloudwatch put-metric-alarm \
  --alarm-name return-abuse-monthly-cost \
  --alarm-description "Alert when monthly cost exceeds $100" \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 21600 \
  --evaluation-periods 1 \
  --threshold 100 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=Currency,Value=USD \
  --region us-east-1
```

### Monitor Costs

```bash
# View cost and usage
aws ce get-cost-and-usage \
  --time-period Start=2026-03-01,End=2026-03-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --filter file://cost-filter.json
```

---

## Cleanup (Delete Everything)

### Delete CloudFormation Stack

```bash
# Delete entire stack
aws cloudformation delete-stack \
  --stack-name return-abuse-prod \
  --region ap-south-1

# Wait for deletion
aws cloudformation wait stack-delete-complete \
  --stack-name return-abuse-prod \
  --region ap-south-1
```

### Manual Cleanup (if not using CloudFormation)

```bash
# Delete Lambda function
aws lambda delete-function \
  --function-name return-abuse-risk-scorer-prod \
  --region ap-south-1

# Delete API Gateway
aws apigateway delete-rest-api \
  --rest-api-id YOUR_API_ID \
  --region ap-south-1

# Delete DynamoDB table
aws dynamodb delete-table \
  --table-name return-abuse-predictions-prod \
  --region ap-south-1

# Delete S3 bucket (must be empty first)
aws s3 rm s3://return-abuse-data-lake-YOUR_ACCOUNT_ID --recursive
aws s3 rb s3://return-abuse-data-lake-YOUR_ACCOUNT_ID

# Delete IAM role
aws iam delete-role \
  --role-name return-abuse-lambda-role-prod
```

---

## Next Steps

1. **Update Landing Page**: Update `index.html` with new API endpoint
2. **Test Integration**: Test with real e-commerce platform
3. **Monitor Performance**: Watch CloudWatch metrics for 24 hours
4. **Optimize Costs**: Review Bedrock usage and consider caching
5. **Add ML Model**: Train SageMaker model for better accuracy

---

**Last Updated**: March 1, 2026  
**Version**: 1.1  
**Support**: punithpunith2001@gmail.com

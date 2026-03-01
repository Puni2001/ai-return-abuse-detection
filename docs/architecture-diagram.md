# AI Return Abuse Detection - System Architecture

## High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         E-COMMERCE PLATFORM                              │
│                    (Order & Return Management System)                    │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 │ HTTPS POST Request
                                 │ (Order/Return Data)
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          AWS API GATEWAY                                 │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  POST /risk-score                                                 │  │
│  │  • CORS Enabled                                                   │  │
│  │  • Rate Limiting                                                  │  │
│  │  • Request Validation                                             │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 │ Invoke
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         AWS LAMBDA FUNCTION                              │
│                    (return-abuse-risk-scorer)                            │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  1. Extract Features                                              │  │
│  │  2. Calculate Risk Score (Rule-Based Model)                       │  │
│  │  3. Generate Explanation (Bedrock)                                │  │
│  │  4. Determine Action                                              │  │
│  │  5. Store Prediction (DynamoDB)                                   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────┬──────────────────────┬──────────────────────┬────────────────────┘
      │                      │                      │
      │                      │                      │
      ▼                      ▼                      ▼
┌──────────────┐   ┌──────────────────┐   ┌──────────────────┐
│   AMAZON     │   │   AMAZON         │   │   AMAZON         │
│   BEDROCK    │   │   DYNAMODB       │   │   S3             │
│              │   │                  │   │                  │
│ Claude 3     │   │ Predictions      │   │ Data Lake        │
│ Sonnet       │   │ Table            │   │                  │
│              │   │                  │   │ • Raw Data       │
│ Generate     │   │ • prediction_id  │   │ • Processed      │
│ Natural      │   │ • order_id       │   │ • Models         │
│ Language     │   │ • risk_score     │   │                  │
│ Explanations │   │ • timestamp      │   │                  │
│              │   │ • explanation    │   │                  │
│              │   │ • TTL (90 days)  │   │                  │
└──────────────┘   └──────────────────┘   └──────────────────┘
                            │
                            │ Query
                            ▼
                   ┌──────────────────┐
                   │   AMAZON         │
                   │   QUICKSIGHT     │
                   │                  │
                   │ Analytics        │
                   │ Dashboard        │
                   │                  │
                   │ • Risk Trends    │
                   │ • Performance    │
                   │ • Business KPIs  │
                   └──────────────────┘
                            │
                            │ View
                            ▼
                   ┌──────────────────┐
                   │   OPERATIONS     │
                   │   TEAM           │
                   │                  │
                   │ • Review Cases   │
                   │ • Take Actions   │
                   │ • Monitor Trends │
                   └──────────────────┘
```

## Data Flow Sequence

### Real-Time Risk Scoring Flow

```
1. E-commerce Platform
   └─> Order/Return Request Created
       └─> POST /risk-score
           {
             "order_id": "ORD123",
             "customer_return_rate": 0.35,
             "total_orders": 12,
             "payment_method": "COD",
             "amount": 8500,
             "product_return_rate": 0.22,
             "is_festival_season": 0
           }

2. API Gateway
   └─> Validate Request
       └─> Route to Lambda

3. Lambda Function
   ├─> Extract Features
   ├─> Calculate Risk Score (Rule-Based)
   │   └─> risk_score = 0.65
   │
   ├─> Call Bedrock (Claude 3 Sonnet)
   │   └─> Generate Natural Language Explanation
   │       └─> "This order shows elevated risk due to..."
   │
   ├─> Determine Action
   │   └─> risk_score 0.3-0.7 → "otp_verification"
   │
   └─> Store in DynamoDB
       └─> prediction_id, timestamp, risk_score, explanation

4. Response to Platform
   {
     "order_id": "ORD123",
     "risk_score": 0.65,
     "risk_level": "medium",
     "recommended_action": "otp_verification",
     "explanation": {
       "generated_by": "bedrock_claude_3_sonnet",
       "explanation_text": "This order requires additional verification..."
     },
     "confidence": 0.3,
     "model_version": "v1.1-bedrock-enhanced"
   }

5. Platform Takes Action
   └─> Medium Risk → Request OTP from Customer
```

## AWS Services Used

### Core Services

| Service | Purpose | Why This Service |
|---------|---------|------------------|
| **AWS Lambda** | Serverless compute for risk scoring | • No server management<br>• Auto-scaling<br>• Pay per request<br>• Sub-second response |
| **Amazon Bedrock** | GenAI for explanations | • Claude 3 Sonnet for natural language<br>• No ML expertise needed<br>• Managed service<br>• Multi-language support |
| **Amazon DynamoDB** | Store predictions | • Millisecond latency<br>• Auto-scaling<br>• TTL for data retention<br>• Global secondary indexes |
| **Amazon API Gateway** | REST API management | • HTTPS endpoints<br>• CORS support<br>• Rate limiting<br>• Request validation |
| **Amazon S3** | Data lake storage | • Unlimited storage<br>• Lifecycle policies<br>• Versioning<br>• Cost-effective |

### Monitoring & Operations

| Service | Purpose |
|---------|---------|
| **CloudWatch** | Logs, metrics, alarms |
| **CloudWatch Dashboard** | Real-time monitoring |
| **QuickSight** | Business intelligence |
| **CloudFormation** | Infrastructure as Code |

## Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SECURITY LAYERS                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. API Gateway                                              │
│     • HTTPS only (TLS 1.2+)                                  │
│     • API keys (optional)                                    │
│     • Rate limiting                                          │
│     • Request validation                                     │
│                                                              │
│  2. IAM Roles & Policies                                     │
│     • Least privilege access                                 │
│     • Lambda execution role                                  │
│     • Bedrock invoke permissions                             │
│     • DynamoDB read/write permissions                        │
│                                                              │
│  3. Data Encryption                                          │
│     • At Rest: S3 (AES-256), DynamoDB (KMS)                  │
│     • In Transit: TLS/SSL                                    │
│                                                              │
│  4. VPC (Optional for Production)                            │
│     • Lambda in private subnet                               │
│     • VPC endpoints for AWS services                         │
│     • Security groups                                        │
│                                                              │
│  5. Audit & Compliance                                       │
│     • CloudTrail for API auditing                            │
│     • CloudWatch Logs for debugging                          │
│     • DynamoDB for prediction audit trail                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Scalability & Performance

### Auto-Scaling Configuration

```
┌─────────────────────────────────────────────────────────────┐
│  Component          │  Scaling Strategy                      │
├─────────────────────┼────────────────────────────────────────┤
│  API Gateway        │  Automatic (10,000 RPS default)        │
│  Lambda             │  Concurrent executions (1000 default)  │
│  DynamoDB           │  On-demand (auto-scales)               │
│  Bedrock            │  Managed by AWS                        │
│  S3                 │  Unlimited                             │
└─────────────────────────────────────────────────────────────┘
```

### Performance Targets

- **API Latency**: < 500ms (p95)
- **Lambda Duration**: < 300ms (without Bedrock), < 2s (with Bedrock)
- **DynamoDB Read/Write**: < 10ms
- **Throughput**: 1000+ requests/second
- **Availability**: 99.9%

## Cost Optimization

### Monthly Cost Estimate (100K requests/month)

```
┌─────────────────────────────────────────────────────────────┐
│  Service            │  Usage              │  Cost           │
├─────────────────────┼─────────────────────┼─────────────────┤
│  Lambda             │  100K invocations   │  $0.20          │
│  API Gateway        │  100K requests      │  $0.35          │
│  Bedrock (Claude)   │  100K calls         │  $30.00         │
│  DynamoDB           │  100K writes        │  $1.25          │
│  S3                 │  10 GB storage      │  $0.23          │
│  CloudWatch         │  Logs & metrics     │  $5.00          │
├─────────────────────┼─────────────────────┼─────────────────┤
│  TOTAL              │                     │  ~$37/month     │
└─────────────────────────────────────────────────────────────┘

Note: First 1M Lambda requests free tier
      First 1M API Gateway requests free tier
```

## Deployment Architecture

### Multi-Environment Setup

```
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│  Development                                                 │
│  └─> CloudFormation Stack: return-abuse-dev                 │
│      └─> API: https://xxx.execute-api.ap-south-1.../dev     │
│                                                              │
│  Staging                                                     │
│  └─> CloudFormation Stack: return-abuse-staging             │
│      └─> API: https://xxx.execute-api.ap-south-1.../staging │
│                                                              │
│  Production                                                  │
│  └─> CloudFormation Stack: return-abuse-prod                │
│      └─> API: https://xxx.execute-api.ap-south-1.../prod    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Future Enhancements (Roadmap)

### Phase 2: ML Model Integration

```
┌─────────────────────────────────────────────────────────────┐
│  Add SageMaker for ML Model Training                         │
│                                                              │
│  S3 Data Lake                                                │
│      ↓                                                       │
│  AWS Glue (ETL)                                              │
│      ↓                                                       │
│  SageMaker Training Job (XGBoost)                            │
│      ↓                                                       │
│  SageMaker Model Registry                                    │
│      ↓                                                       │
│  SageMaker Endpoint (Real-time Inference)                    │
│      ↓                                                       │
│  Lambda calls SageMaker instead of rule-based               │
└─────────────────────────────────────────────────────────────┘
```

### Phase 3: Advanced Analytics

- Real-time streaming with Kinesis
- Advanced dashboards with QuickSight
- A/B testing framework
- Model monitoring with SageMaker Model Monitor

## Key Differentiators

### Why This Architecture?

1. **Serverless-First**: No server management, auto-scaling, pay-per-use
2. **GenAI Integration**: Bedrock for natural language explanations
3. **India-Specific**: Deployed in ap-south-1 (Mumbai) for low latency
4. **Production-Ready**: Monitoring, alarms, audit trails built-in
5. **Cost-Effective**: ~$37/month for 100K requests
6. **Scalable**: Handles 1000+ RPS without changes

---

**Last Updated**: March 1, 2026  
**Version**: 1.1 (Bedrock-Enhanced)  
**Team**: Soul | Punith S

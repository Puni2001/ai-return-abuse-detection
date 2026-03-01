# AI Return Abuse Detection System

**Team:** Soul  
**Team Leader:** Punith S

🔗 **Live Demo**: [Try it now!](https://your-netlify-url.netlify.app)  
📊 **Dashboard**: [View Analytics](https://your-netlify-url.netlify.app/dashboard.html)  
🔌 **API Endpoint**: `https://nglukkm7m9.execute-api.ap-south-1.amazonaws.com/prod/risk-score`

## Overview

An intelligent, proactive AI system designed to predict and prevent return abuse in e-commerce before losses occur, while maintaining a positive experience for genuine customers. The system leverages machine learning and India-specific behavioral signals to provide real-time risk assessment and explainable decision-making.

### 🎥 Quick Demo
Visit our [live demo](https://your-netlify-url.netlify.app) to test the system with pre-configured scenarios:
- **Low Risk**: Trusted customer with good history
- **Medium Risk**: New customer with COD payment
- **High Risk**: Suspicious pattern detected

## Problem Statement

E-commerce platforms face significant challenges with return abuse:
- 10–40% of returns are abusive or avoidable
- Existing systems only detect abuse after losses occur
- Static rule-based systems often hurt genuine customers
- Returns increase logistics costs, inventory damage, and seller losses

## Solution

Our AI-powered system provides:
- **Proactive Risk Assessment**: Predicts return abuse risk at order placement and return initiation
- **Explainable AI**: Generates transparent risk scores with clear reasoning
- **Graduated Actions**: Implements risk-appropriate responses without blanket blocking
- **Bharat-Specific Intelligence**: Incorporates India-specific behavioral patterns and festival dynamics

## Key Features

### 🎯 Intelligent Risk Scoring
- Real-time Return Abuse Risk Score (0–1) for each order/return
- Multi-dimensional behavior analysis (customer, product, seller)
- Explainable AI with clear reasoning for decisions

### 🇮🇳 India-Specific Intelligence
- Festival and sale season abuse detection
- COD (Cash on Delivery) pattern analysis
- Regional behavior variations
- Local market dynamics integration

### ⚡ Action Recommendation Engine
- **Low Risk (0.0-0.3)**: Instant refund processing
- **Medium Risk (0.3-0.7)**: OTP/Extra verification required
- **High Risk (0.7-1.0)**: Refund after quality check inspection

### 📊 Operations Dashboard
- Real-time risk monitoring
- Abuse trend analysis
- Performance metrics tracking
- Configurable alerts and reporting

## Architecture

### Technology Stack
- **Cloud Platform**: AWS
- **ML/AI**: SageMaker, Lambda
- **Data Storage**: S3, DynamoDB
- **Data Processing**: AWS Glue
- **API Management**: API Gateway
- **Monitoring**: CloudWatch, QuickSight

### System Components
1. **Data Ingestion Layer**: Real-time streaming and batch processing
2. **ML Pipeline**: Feature engineering, model training, and inference
3. **Decision Engine**: Risk-based action recommendations
4. **API Layer**: Real-time scoring and batch processing endpoints
5. **Dashboard**: Operations monitoring and analytics

## Getting Started

### 🚀 Try the Live Demo
1. Visit: [Live Demo](https://your-netlify-url.netlify.app)
2. Click one of the quick test buttons (Low/Medium/High Risk)
3. Click "Check Risk Score" to see real-time API response
4. View risk score, recommended action, and explanations

### 🔧 Local Development

#### Prerequisites
- AWS Account with appropriate permissions
- Python 3.11+
- AWS CLI configured

#### Setup
```bash
# Clone the repository
git clone https://github.com/Puni2001/ai-return-abuse-detection.git
cd ai-return-abuse-detection

# Test the Lambda function locally
python lambda_function.py

# Open the demo page
open index.html
```

### ☁️ AWS Deployment

#### Lambda Function
1. Go to AWS Lambda Console
2. Create function: `return-abuse-risk-scorer`
3. Runtime: Python 3.11
4. Copy code from `lambda_function.py`
5. Deploy

#### API Gateway
1. Create REST API
2. Create POST method `/risk-score`
3. Link to Lambda function
4. Enable CORS
5. Deploy to stage

## API Usage

### Risk Scoring Endpoint
```
POST https://nglukkm7m9.execute-api.ap-south-1.amazonaws.com/prod/risk-score
Content-Type: application/json
```

### Request Example
```json
{
  "order_id": "ORD123456",
  "customer_return_rate": 0.35,
  "total_orders": 12,
  "payment_method": "COD",
  "amount": 8500,
  "product_return_rate": 0.22,
  "is_festival_season": 0
}
```

### Response Example
```json
{
  "order_id": "ORD123456",
  "risk_score": 0.65,
  "risk_level": "medium",
  "recommended_action": "otp_verification",
  "explanation": {
    "top_factors": [
      "High return rate: 35% of orders returned",
      "Cash on Delivery payment method (higher risk)",
      "Product has elevated return rate: 22%"
    ]
  },
  "confidence": 0.3,
  "model_version": "v1.0-rule-based"
}
```

### Test with cURL
```bash
curl -X POST https://nglukkm7m9.execute-api.ap-south-1.amazonaws.com/prod/risk-score \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "TEST001",
    "customer_return_rate": 0.15,
    "total_orders": 25,
    "payment_method": "Prepaid",
    "amount": 2500,
    "product_return_rate": 0.10,
    "is_festival_season": 1
  }'
```

## Project Structure

```
ai-return-abuse-detection/
├── lambda_function.py          # AWS Lambda function (risk scoring logic)
├── index.html                  # Live demo interface
├── demo.html                   # Alternative demo page
├── dashboard.html              # Analytics dashboard
├── sample-data/                # Sample datasets
│   ├── customers.csv
│   ├── orders.csv
│   ├── products.csv
│   ├── returns.csv
│   └── generate_realistic_india_data.py
├── scripts/
│   └── upload-to-s3.sh        # S3 upload helper
├── requirements.md             # Detailed requirements
├── design.md                   # Technical architecture
├── aws-implementation-plan.md  # AWS setup guide
└── README.md                   # This file
```

## Performance Metrics

### Current Implementation
- **API Response Time**: ~2ms (Lambda cold start: ~120ms)
- **Model**: Rule-based algorithm (v1.0)
- **Cost**: $0/month (AWS Free Tier)
- **Uptime**: 99.9%+ (AWS Lambda)

### Business Impact (Projected)
- **Target**: 25-40% reduction in return losses
- **Customer Experience**: Maintained satisfaction for genuine customers
- **Operational Efficiency**: Reduced manual review workload

### Technical Metrics (Target for ML Model)
- **Model Accuracy**: >85% (current: rule-based)
- **API Response Time**: <500ms (current: ~2ms)
- **System Uptime**: >99.9% (current: 99.9%+)
- **Data Processing Latency**: <5 minutes

## Key Differentiators

- **Proactive vs Reactive**: Prevents abuse before it occurs
- **Hybrid Approach**: Combines ML intelligence with business rules
- **Multi-dimensional**: Analyzes customer, product, and seller patterns
- **India-Aware**: Incorporates local behavioral signals
- **Explainable**: Provides transparent decision reasoning

## Documentation

- [Requirements](requirements.md) - Detailed functional and technical requirements
- [Design](design.md) - Technical architecture and implementation details
- [AWS Implementation Plan](aws-implementation-plan.md) - AWS services and setup
- [Cost Estimate](aws-cost-estimate.md) - AWS cost breakdown
- [Build Roadmap](BUILD-AND-LAUNCH-ROADMAP.md) - 12-week implementation plan

## Technology Stack

**Current Implementation:**
- AWS Lambda (Python 3.11) - Serverless compute
- API Gateway - REST API management
- Netlify - Frontend hosting
- GitHub - Version control

**Planned Enhancements:**
- Amazon SageMaker - ML model training
- Amazon S3 - Data lake
- DynamoDB - Predictions storage
- Amazon Bedrock - Enhanced AI explanations
- QuickSight - Advanced analytics

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For questions and support:
- 📧 Email: punithpunith2001@gmail.com
- 💻 GitHub: [Create an issue](https://github.com/Puni2001/ai-return-abuse-detection/issues)
- 🔗 LinkedIn: [Connect with team lead](https://linkedin.com/in/punith-s)

---

**Built with ❤️ by Team Soul for Hackathon 2026**
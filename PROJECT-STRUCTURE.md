# Project Structure

## AI Return Abuse Detection System

```
ai-return-abuse-detection/
│
├── README.md                           # Main project documentation
├── PROJECT-STRUCTURE.md                # This file - project organization
├── .gitignore                          # Git ignore rules
│
├── index.html                          # Live demo web interface
├── lambda_function.py                  # AWS Lambda function (main API)
├── cloudformation-template.yaml        # AWS infrastructure as code
│
├── deploy-all.sh                       # Main deployment script
├── deploy-sagemaker-optional.sh        # Optional SageMaker deployment
├── update-lambda.sh                    # Lambda update script
├── test-complete-system.sh             # Comprehensive system tests
│
├── docs/                               # Documentation
│   ├── DEPLOYMENT-GUIDE.md             # Step-by-step deployment
│   ├── architecture-diagram.md         # System architecture
│   ├── design.md                       # Design decisions
│   ├── requirements.md                 # System requirements
│   ├── aws-cost-estimate.md            # Cost analysis
│   └── AI_Return_Abuse_Detection.pdf   # Project presentation
│
├── sagemaker-training/                 # ML model training
│   ├── train.py                        # Training script
│   ├── deploy-sagemaker.py             # SageMaker deployment
│   └── requirements.txt                # Python dependencies
│
├── sample-data/                        # Test data
│   ├── customers.csv                   # Sample customer data
│   ├── orders.csv                      # Sample order data
│   ├── products.csv                    # Sample product data
│   ├── returns.csv                     # Sample return data
│   ├── generate_data.py                # Data generator
│   └── generate_realistic_india_data.py # India-specific data
│
└── scripts/                            # Utility scripts
    └── upload-to-s3.sh                 # S3 upload helper
```

## Key Components

### Core Application
- **lambda_function.py**: Main API logic with hybrid ML architecture
- **index.html**: Interactive demo interface
- **cloudformation-template.yaml**: Complete AWS infrastructure

### Deployment
- **deploy-all.sh**: One-command deployment
- **update-lambda.sh**: Quick Lambda updates
- **test-complete-system.sh**: Automated testing

### Documentation
- **README.md**: Project overview and quick start
- **docs/**: Comprehensive technical documentation

### Machine Learning
- **sagemaker-training/**: ML model training and deployment
- **sample-data/**: Training and testing datasets

## AWS Services Used

1. **AWS Lambda** - Serverless API
2. **API Gateway** - REST API endpoint
3. **DynamoDB** - Audit trail storage
4. **S3** - Data storage
5. **CloudWatch** - Monitoring and logging
6. **SageMaker** - ML model hosting
7. **Bedrock** - AI explanations (Claude Sonnet 4)

## Quick Start

```bash
# 1. Deploy infrastructure
./deploy-all.sh

# 2. Test the system
./test-complete-system.sh

# 3. Open index.html in browser for demo
```

## Team

- **Punith S** - Lead Developer
- **Yadoji Muralidhar Bokare** - Testing & Validation

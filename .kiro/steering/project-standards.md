---
inclusion: always
---

# Project Standards - AI Return Abuse Detection System

## Project Context
This is an AI-powered return abuse detection system for e-commerce platforms, focusing on Indian market dynamics. The system uses AWS services and machine learning to predict return abuse risk proactively.

## Code Standards

### Python Code Style
- Follow PEP 8 guidelines
- Use type hints for function parameters and return values
- Maximum line length: 100 characters
- Use meaningful variable names that reflect business domain (e.g., `risk_score`, `customer_profile`)

### AWS Best Practices
- Use Infrastructure as Code (CloudFormation/CDK)
- Implement least privilege IAM policies
- Enable encryption at rest and in transit
- Tag all resources with: `Project`, `Environment`, `Team`

### Machine Learning Standards
- Document model assumptions and limitations
- Track model versions in SageMaker Model Registry
- Include SHAP values for explainability
- Monitor model drift and performance metrics

## Documentation Requirements
- All API endpoints must have OpenAPI/Swagger documentation
- Include example requests and responses
- Document risk thresholds and business rules
- Maintain changelog for model updates

## Testing Requirements
- Unit tests for business logic
- Integration tests for API endpoints
- Model performance tests (accuracy, latency)
- Load testing for peak traffic scenarios

## Security & Compliance
- Never log PII data
- Anonymize customer data in development environments
- Implement audit trails for all risk decisions
- Follow data retention policies

## India-Specific Considerations
- Account for festival seasons (Diwali, Holi, etc.)
- Consider COD payment patterns
- Regional behavior variations across states
- Local language support for customer communications

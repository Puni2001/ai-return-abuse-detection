---
inclusion: fileMatch
fileMatchPattern: '**/*.{py,ipynb}'
---

# Machine Learning Development Guidelines

## Model Development Workflow

### 1. Feature Engineering
- Extract customer, product, and seller features
- Include temporal features (time since last order, return frequency)
- Add India-specific features (festival indicators, COD flags, regional patterns)
- Document feature definitions and business logic

### 2. Model Training
- Use XGBoost or LightGBM for gradient boosting
- Implement cross-validation (5-fold minimum)
- Track experiments with SageMaker Experiments
- Save feature importance and SHAP values

### 3. Model Evaluation
- Primary metric: AUC-ROC (target >0.85)
- Monitor precision-recall trade-offs
- Evaluate false positive rate impact on genuine customers
- Test on India-specific scenarios (festivals, sales)

### 4. Model Deployment
- Use SageMaker endpoints with auto-scaling
- Implement A/B testing for new models
- Set up CloudWatch alarms for latency and errors
- Document rollback procedures

## Explainability Requirements
- Generate SHAP values for each prediction
- Provide top 3-5 risk factors in API response
- Use business-friendly language in explanations
- Ensure explanations are actionable for operations team

## Monitoring & Maintenance
- Track model performance metrics daily
- Monitor data drift using SageMaker Model Monitor
- Retrain models monthly or when drift detected
- Maintain model performance dashboard

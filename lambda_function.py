"""
AI Return Abuse Detection System - Lambda Function

This Lambda function provides a REST API for predicting return abuse risk in e-commerce
transactions. It uses a hybrid architecture combining:
- Amazon SageMaker ML models for accurate predictions
- Amazon Bedrock (Claude Sonnet 4) for AI-powered explanations
- Rule-based fallback system for 100% uptime

Features:
- Real-time risk scoring (0.0 to 1.0)
- Risk level classification (low/medium/high)
- Explainable AI with top risk factors
- DynamoDB audit trail
- Automatic fallback mechanisms

Author: Punith S
Version: 1.2-hybrid
"""

import json
import boto3
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any

# Initialize AWS clients
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
sagemaker_runtime = boto3.client('sagemaker-runtime', region_name='ap-south-1')
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')

# Configuration from environment variables
PREDICTIONS_TABLE = os.environ.get('PREDICTIONS_TABLE', 'return-abuse-predictions')
SAGEMAKER_ENDPOINT = os.environ.get('SAGEMAKER_ENDPOINT', 'return-abuse-prod-endpoint')

# Model version tracking
MODEL_VERSION = 'v1.2-hybrid'

def predict_with_sagemaker(features: Dict[str, Any]) -> Tuple[Optional[float], List]:
    """
    Use Amazon SageMaker endpoint for ML-based risk prediction.
    
    Args:
        features: Dictionary containing customer and order features
        
    Returns:
        Tuple of (risk_score, feature_importance)
        Returns (None, []) if SageMaker is unavailable
        
    Features used:
        - customer_return_rate: Historical return rate (0.0-1.0)
        - total_orders: Number of previous orders
        - is_cod: Cash on Delivery flag (0 or 1)
        - amount: Order value in INR
        - product_return_rate: Product category return rate
        - is_festival_season: Festival season indicator (0 or 1)
    """
    try:
        if not SAGEMAKER_ENDPOINT:
            return None, []
        
        # Prepare features for SageMaker (XGBoost CSV format)
        feature_vector = [
            features['customer_return_rate'],
            features['total_orders'],
            features['is_cod'],
            features['amount'],
            features['product_return_rate'],
            features['is_festival_season']
        ]
        
        # Call SageMaker endpoint
        response = sagemaker_runtime.invoke_endpoint(
            EndpointName=SAGEMAKER_ENDPOINT,
            ContentType='text/csv',
            Body=','.join(map(str, feature_vector))
        )
        
        # Parse prediction - SageMaker returns a simple float value
        result = response['Body'].read().decode().strip()
        risk_score = float(result)
        
        # Feature importance not available from basic XGBoost endpoint
        # Consider using SageMaker Clarify for SHAP values in production
        feature_importance = []
        
        return risk_score, feature_importance
        
    except Exception as e:
        print(f"SageMaker prediction error: {str(e)}")
        return None, None


def calculate_risk_score(features: Dict[str, Any]) -> float:
    """
    Rule-based risk scoring algorithm (fallback when SageMaker unavailable).
    
    This algorithm uses weighted factors based on e-commerce domain expertise
    and Indian market patterns.
    
    Args:
        features: Dictionary containing customer and order features
        
    Returns:
        Risk score between 0.0 and 1.0
        
    Risk Factors:
        - Customer return rate (40% weight)
        - Order history and value (30% weight)
        - Payment method - COD risk (15% weight)
        - Product category risk (10% weight)
        - Festival season patterns (5% weight)
    """
    customer_return_rate = features['customer_return_rate']
    total_orders = features['total_orders']
    is_cod = features['is_cod']
    amount = features['amount']
    product_return_rate = features['product_return_rate']
    is_festival_season = features['is_festival_season']
    
    # Base risk score
    risk_score = 0.0
    risk_factors = []
    
    # Customer behavior factors (40% weight)
    if customer_return_rate > 0.5:
        risk_score += 0.30
        risk_factors.append({
            'factor': 'very_high_customer_return_rate',
            'value': customer_return_rate,
            'weight': 0.30
        })
    elif customer_return_rate > 0.3:
        risk_score += 0.15
        risk_factors.append({
            'factor': 'high_customer_return_rate',
            'value': customer_return_rate,
            'weight': 0.15
        })
    elif customer_return_rate > 0.15:
        risk_score += 0.05
        risk_factors.append({
            'factor': 'moderate_customer_return_rate',
            'value': customer_return_rate,
            'weight': 0.05
        })
    
    # New customer risk (10% weight)
    if total_orders < 3:
        risk_score += 0.10
        risk_factors.append({
            'factor': 'new_customer',
            'value': total_orders,
            'weight': 0.10
        })
    elif total_orders < 10:
        risk_score += 0.05
        risk_factors.append({
            'factor': 'relatively_new_customer',
            'value': total_orders,
            'weight': 0.05
        })
    
    # Payment method risk (15% weight)
    if is_cod:
        risk_score += 0.15
        risk_factors.append({
            'factor': 'cod_payment',
            'value': 'COD',
            'weight': 0.15
        })
    
    # High value order risk (20% weight)
    if amount > 50000:
        risk_score += 0.20
        risk_factors.append({
            'factor': 'very_high_value_order',
            'value': amount,
            'weight': 0.20
        })
    elif amount > 20000:
        risk_score += 0.10
        risk_factors.append({
            'factor': 'high_value_order',
            'value': amount,
            'weight': 0.10
        })
    elif amount > 10000:
        risk_score += 0.05
        risk_factors.append({
            'factor': 'moderate_value_order',
            'value': amount,
            'weight': 0.05
        })
    
    # Product return pattern (10% weight)
    if product_return_rate > 0.4:
        risk_score += 0.10
        risk_factors.append({
            'factor': 'high_product_return_rate',
            'value': product_return_rate,
            'weight': 0.10
        })
    elif product_return_rate > 0.2:
        risk_score += 0.05
        risk_factors.append({
            'factor': 'moderate_product_return_rate',
            'value': product_return_rate,
            'weight': 0.05
        })
    
    # Festival season adjustment (5% weight - reduces risk)
    if is_festival_season:
        risk_score -= 0.05
        risk_factors.append({
            'factor': 'festival_season',
            'value': 'Yes',
            'weight': -0.05
        })
    
    # Normalize to 0-1 range
    risk_score = max(0.0, min(1.0, risk_score))
    
    return risk_score, risk_factors


def generate_bedrock_explanation(
    risk_score: float, 
    risk_factors: List[Dict], 
    features: Dict[str, Any]
) -> Tuple[str, str]:
    """
    Use Amazon Bedrock (Claude Sonnet 4) to generate AI-powered explanations.
    
    Args:
        risk_score: Calculated risk score (0.0-1.0)
        risk_factors: List of detected risk factors
        features: Order and customer features
        
    Returns:
        Tuple of (explanation_text, generated_by)
        Falls back to rule-based explanation if Bedrock unavailable
        
    Note:
        Uses Claude Sonnet 4 inference profile for consistent performance
        across regions. Explanation includes risk summary, key factors,
        and actionable recommendations.
    """
    try:
        # Prepare context for Bedrock
        prompt = f"""You are an AI assistant for an e-commerce return abuse detection system. 
Generate a clear, professional explanation for the following return risk assessment.

Risk Score: {risk_score:.2f} (0 = No Risk, 1 = High Risk)

Risk Factors Detected:
{json.dumps(risk_factors, indent=2)}

Order Details:
- Customer Return Rate: {features['customer_return_rate']*100:.1f}%
- Total Orders: {features['total_orders']}
- Payment Method: {'COD' if features['is_cod'] else 'Prepaid'}
- Order Amount: ₹{features['amount']:,.0f}
- Product Return Rate: {features['product_return_rate']*100:.1f}%
- Festival Season: {'Yes' if features['is_festival_season'] else 'No'}

Generate:
1. A brief summary (1-2 sentences) explaining the risk level
2. Top 3-5 key factors contributing to this risk score
3. A recommended action for the operations team

Keep the language professional, clear, and actionable. Focus on business impact."""

        # Call Bedrock API using cross-region inference profile
        # Using Claude Sonnet 4 (latest and most capable)
        response = bedrock_runtime.invoke_model(
            modelId='us.anthropic.claude-sonnet-4-20250514-v1:0',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 500,
                'messages': [{
                    'role': 'user',
                    'content': prompt
                }],
                'temperature': 0.3
            })
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        explanation_text = response_body['content'][0]['text']
        
        return {
            'generated_by': 'bedrock_claude_3_sonnet',
            'explanation_text': explanation_text,
            'risk_factors': risk_factors
        }
        
    except Exception as e:
        # Fallback to rule-based explanation if Bedrock fails
        print(f"Bedrock error: {str(e)}")
        return generate_fallback_explanation(risk_score, risk_factors, features)


def generate_fallback_explanation(
    risk_score: float, 
    risk_factors: List[Dict], 
    features: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate rule-based explanation when Bedrock is unavailable.
    
    Args:
        risk_score: Calculated risk score
        risk_factors: List of detected risk factors
        features: Order and customer features
        
    Returns:
        Dictionary with explanation text and top factors
        
    Note:
        Provides business-friendly explanations for each risk factor
        with India-specific context (COD, festival seasons, etc.)
    """
    reasons = []
    
    for factor in risk_factors:
        if factor['factor'] == 'very_high_customer_return_rate':
            reasons.append(f"Very high return rate: {factor['value']*100:.0f}% of orders returned")
        elif factor['factor'] == 'high_customer_return_rate':
            reasons.append(f"High return rate: {factor['value']*100:.0f}% of orders returned")
        elif factor['factor'] == 'new_customer':
            reasons.append(f"New customer with only {factor['value']} previous orders")
        elif factor['factor'] == 'cod_payment':
            reasons.append("Cash on Delivery payment method (higher risk)")
        elif factor['factor'] == 'very_high_value_order':
            reasons.append(f"Very high value order: ₹{factor['value']:,.0f}")
        elif factor['factor'] == 'high_value_order':
            reasons.append(f"High value order: ₹{factor['value']:,.0f}")
        elif factor['factor'] == 'high_product_return_rate':
            reasons.append(f"Product has high return rate: {factor['value']*100:.0f}%")
        elif factor['factor'] == 'festival_season':
            reasons.append("Festival season - normal shopping behavior expected")
    
    if not reasons:
        reasons = ["Normal return pattern with no significant risk indicators"]
    
    return {
        'generated_by': 'rule_based_fallback',
        'explanation_text': ' | '.join(reasons[:5]),
        'top_factors': reasons[:5]
    }


def store_prediction_dynamodb(prediction_data: Dict[str, Any]) -> None:
    """
    Store prediction in DynamoDB for audit trail and analytics.
    
    Args:
        prediction_data: Complete prediction result including risk score,
                        factors, and metadata
                        
    Note:
        - Enables compliance and audit requirements
        - Supports model performance monitoring
        - TTL set to 90 days for automatic cleanup
        - No PII data stored (order IDs only)
    """
    try:
        table = dynamodb.Table(PREDICTIONS_TABLE)
        
        item = {
            'prediction_id': f"{prediction_data['order_id']}_{int(datetime.now().timestamp())}",
            'order_id': prediction_data['order_id'],
            'timestamp': datetime.now().isoformat(),
            'risk_score': str(prediction_data['risk_score']),
            'risk_level': prediction_data['risk_level'],
            'recommended_action': prediction_data['recommended_action'],
            'explanation': json.dumps(prediction_data['explanation']),
            'model_version': prediction_data['model_version'],
            'ttl': int(datetime.now().timestamp()) + (90 * 24 * 60 * 60)  # 90 days retention
        }
        
        table.put_item(Item=item)
        return True
    except Exception as e:
        print(f"DynamoDB error: {str(e)}")
        return False


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for return abuse risk prediction API.
    
    Args:
        event: API Gateway event containing request body
        context: Lambda context object
        
    Returns:
        API Gateway response with risk prediction
        
    Request Body:
        {
            "order_id": "string",
            "customer_return_rate": float (0.0-1.0),
            "total_orders": int,
            "payment_method": "COD" | "Prepaid",
            "amount": float (INR),
            "product_return_rate": float (0.0-1.0),
            "is_festival_season": 0 | 1
        }
        
    Response:
        {
            "risk_score": float (0.0-1.0),
            "risk_level": "low" | "medium" | "high",
            "confidence": float (0.0-1.0),
            "recommended_action": string,
            "explanation": {
                "generated_by": "sagemaker_ml" | "bedrock_claude_3_sonnet" | "rule_based_fallback",
                "explanation_text": string,
                "top_factors": [string]
            },
            "model_type": "sagemaker_ml" | "rule_based",
            "model_version": string,
            "timestamp": ISO datetime
        }
    """
    try:
        # Parse input
        if 'body' in event:
            body = json.loads(event['body'])
        else:
            body = event
        
        # Extract features
        features = {
            'customer_return_rate': body.get('customer_return_rate', 0.0),
            'total_orders': body.get('total_orders', 0),
            'is_cod': 1 if (body.get('payment_method') == 'COD' or body.get('is_cod') == True or body.get('is_cod') == 1) else 0,
            'amount': body.get('amount', 0),
            'product_return_rate': body.get('product_return_rate', 0.0),
            'is_festival_season': 1 if (body.get('is_festival_season') == True or body.get('is_festival_season') == 1) else 0
        }
        
        # Try SageMaker first, fallback to rule-based
        risk_score, feature_importance = predict_with_sagemaker(features)
        
        if risk_score is not None:
            # SageMaker prediction successful
            model_type = 'sagemaker_ml'
            risk_factors = feature_importance if feature_importance else []
        else:
            # Fallback to rule-based model
            model_type = 'rule_based'
            risk_score, risk_factors = calculate_risk_score(features)
        
        # Generate explanation using Bedrock (with fallback)
        use_bedrock = body.get('use_bedrock', True)
        if use_bedrock:
            explanation = generate_bedrock_explanation(risk_score, risk_factors, features)
        else:
            explanation = generate_fallback_explanation(risk_score, risk_factors, features)
        
        # Determine action based on risk level
        if risk_score < 0.3:
            risk_level = 'low'
            action = 'instant_refund'
        elif risk_score < 0.7:
            risk_level = 'medium'
            action = 'otp_verification'
        else:
            risk_level = 'high'
            action = 'quality_check_required'
        
        # Build response
        response_body = {
            'order_id': body.get('order_id', 'unknown'),
            'risk_score': round(risk_score, 3),
            'risk_level': risk_level,
            'recommended_action': action,
            'explanation': explanation,
            'confidence': round(abs(risk_score - 0.5) * 2, 3),
            'model_version': 'v1.2-hybrid',
            'model_type': model_type,
            'timestamp': datetime.now().isoformat()
        }
        
        # Store prediction in DynamoDB
        store_prediction_dynamodb(response_body)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            'body': json.dumps(response_body)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': str(e),
                'message': 'Internal server error'
            })
        }

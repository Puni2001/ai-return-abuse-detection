import json
import boto3
import os
from datetime import datetime

# Initialize AWS clients
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')

# DynamoDB table name (will be created via CloudFormation)
PREDICTIONS_TABLE = os.environ.get('PREDICTIONS_TABLE', 'return-abuse-predictions')

def calculate_risk_score(features):
    """
    Rule-based risk scoring algorithm
    Returns risk score between 0 and 1
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


def generate_bedrock_explanation(risk_score, risk_factors, features):
    """
    Use Amazon Bedrock (Claude 3 Sonnet) to generate human-readable explanation
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

        # Call Bedrock API with Claude Sonnet 4 (newest, most capable model)
        response = bedrock_runtime.invoke_model(
            modelId='anthropic.claude-sonnet-4-20250514-v1:0',
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


def generate_fallback_explanation(risk_score, risk_factors, features):
    """
    Fallback explanation if Bedrock is unavailable
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


def store_prediction_dynamodb(prediction_data):
    """
    Store prediction in DynamoDB for audit trail and analytics
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


def lambda_handler(event, context):
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
            'is_cod': 1 if body.get('payment_method') == 'COD' else 0,
            'amount': body.get('amount', 0),
            'product_return_rate': body.get('product_return_rate', 0.0),
            'is_festival_season': body.get('is_festival_season', 0)
        }
        
        # Calculate risk score using rule-based model
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
            'model_version': 'v1.1-bedrock-enhanced',
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

import json

def calculate_risk_score(features):
    """
    Rule-based risk scoring algorithm (mock ML model for hackathon demo)
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
    
    # Customer behavior factors (40% weight)
    if customer_return_rate > 0.5:
        risk_score += 0.30
    elif customer_return_rate > 0.3:
        risk_score += 0.15
    elif customer_return_rate > 0.15:
        risk_score += 0.05
    
    # New customer risk (10% weight)
    if total_orders < 3:
        risk_score += 0.10
    elif total_orders < 10:
        risk_score += 0.05
    
    # Payment method risk (15% weight)
    if is_cod:
        risk_score += 0.15
    
    # High value order risk (20% weight)
    if amount > 50000:
        risk_score += 0.20
    elif amount > 20000:
        risk_score += 0.10
    elif amount > 10000:
        risk_score += 0.05
    
    # Product return pattern (10% weight)
    if product_return_rate > 0.4:
        risk_score += 0.10
    elif product_return_rate > 0.2:
        risk_score += 0.05
    
    # Festival season adjustment (5% weight - reduces risk)
    if is_festival_season:
        risk_score -= 0.05
    
    # Normalize to 0-1 range
    risk_score = max(0.0, min(1.0, risk_score))
    
    return risk_score


def generate_explanation(features, risk_score):
    """
    Generate human-readable explanation for the risk score
    Returns top risk factors in business-friendly language
    """
    reasons = []
    
    # Analyze each factor
    if features['customer_return_rate'] > 0.5:
        reasons.append(f"Very high return rate: {features['customer_return_rate']*100:.0f}% of orders returned")
    elif features['customer_return_rate'] > 0.3:
        reasons.append(f"High return rate: {features['customer_return_rate']*100:.0f}% of orders returned")
    
    if features['total_orders'] < 3:
        reasons.append(f"New customer with only {features['total_orders']} previous orders")
    
    if features['is_cod']:
        reasons.append("Cash on Delivery payment method (higher risk)")
    
    if features['amount'] > 50000:
        reasons.append(f"Very high value order: ₹{features['amount']:,.0f}")
    elif features['amount'] > 20000:
        reasons.append(f"High value order: ₹{features['amount']:,.0f}")
    
    if features['product_return_rate'] > 0.4:
        reasons.append(f"Product has high return rate: {features['product_return_rate']*100:.0f}%")
    
    if features['is_festival_season']:
        reasons.append("Festival season - normal shopping behavior expected")
    
    # Return top 3-5 reasons
    if not reasons:
        return ["Normal return pattern with no significant risk indicators"]
    
    return reasons[:5]


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
        risk_score = calculate_risk_score(features)
        
        # Generate explanation
        explanation = generate_explanation(features, risk_score)
        
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
            'explanation': {
                'top_factors': explanation
            },
            'confidence': round(abs(risk_score - 0.5) * 2, 3),  # Higher confidence at extremes
            'model_version': 'v1.0-rule-based'
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response_body)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

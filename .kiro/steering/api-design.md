---
inclusion: fileMatch
fileMatchPattern: '**/*api*.{py,js,ts,yaml,json}'
---

# API Design Guidelines

## REST API Standards

### Endpoint Naming
- Use kebab-case for URLs: `/api/v1/risk-score`
- Use nouns for resources, verbs for actions
- Version all APIs: `/api/v1/`, `/api/v2/`

### Request/Response Format
- Use JSON for all requests and responses
- Include request validation with clear error messages
- Return appropriate HTTP status codes
- Include correlation IDs for request tracking

### Error Handling
```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Customer ID is required",
    "correlation_id": "abc-123-def"
  }
}
```

### Performance Requirements
- API response time: <500ms (p95)
- Implement request caching where appropriate
- Use pagination for list endpoints
- Rate limiting: 1000 requests/minute per client

## Risk Scoring API Specification

### Request Structure
- Required fields: `order_id`, `customer_id`, `product_id`
- Optional fields: `order_details`, `context`
- Validate all inputs before processing

### Response Structure
- Always include: `risk_score`, `risk_level`, `recommended_action`
- Provide `explanation` with top risk factors
- Include `confidence` score
- Add `processing_time_ms` for monitoring

## Security
- Require API key authentication
- Implement rate limiting per client
- Log all requests (without PII)
- Use HTTPS only

# Conflict Zero API Documentation

## Base URL
- Development: `http://localhost:8000`
- Production: `https://api.conflictzero.com`

## Authentication
All endpoints (except `/health`, `/api/v1/auth/login`, `/api/v1/auth/register`) require a Bearer token in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

## Endpoints Overview

### Health & Status
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/health` | Health check for Render/Docker | No |
| GET | `/api/v2/status` | Detailed API status | No |

### Authentication
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/auth/login` | Login with email/password | No |
| POST | `/api/v1/auth/register` | Register new company | No |
| GET | `/api/v1/auth/me` | Get current user info | Yes |
| POST | `/api/v1/auth/refresh` | Refresh JWT token | Yes |

### Verifications
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/verify` | Verify a single RUC | Yes |
| GET | `/api/v1/verifications/history` | Get verification history | Yes |
| GET | `/api/v1/verifications/{id}` | Get verification by ID | Yes |
| GET | `/api/v1/verifications/{id}/certificate` | Get verification certificate | Yes |

### Compare
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/compare` | Compare 2-10 RUCs | Yes |
| GET | `/api/v1/compare/history` | Get comparison history | Yes |

### Company
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/company/profile` | Get company profile | Yes |
| PATCH | `/api/v1/company/profile` | Update company profile | Yes |
| GET | `/api/v1/company/public-profile` | Get public profile | Yes |
| GET | `/api/v1/company/api-keys` | List API keys | Yes |
| POST | `/api/v1/company/api-keys` | Create new API key | Yes |
| DELETE | `/api/v1/company/api-keys/{id}` | Revoke API key | Yes |

### Invites
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v2/invites` | List invites | Yes |
| POST | `/api/v2/invites` | Create new invite | Yes |
| GET | `/api/v2/invites/stats` | Get invite stats | Yes |
| POST | `/api/v2/invites/{id}/resend` | Resend invite | Yes |

### Compliance (Founder Program)
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v2/founder/compliance` | Get compliance status | Yes |
| GET | `/api/v2/founder/obligations` | Get obligations | Yes |
| GET | `/api/v2/founder/network` | Get network status | Yes |

### Network (Mi Red - Supplier Network)
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v2/network/` | List suppliers | Yes |
| POST | `/api/v2/network/add` | Add supplier | Yes |
| GET | `/api/v2/network/{id}` | Get supplier details | Yes |
| PATCH | `/api/v2/network/{id}` | Update supplier | Yes |
| DELETE | `/api/v2/network/{id}` | Remove supplier | Yes |
| GET | `/api/v2/network/alerts` | Get alerts | Yes |
| PATCH | `/api/v2/network/alerts/{id}/read` | Mark alert as read | Yes |
| POST | `/api/v2/network/alerts/mark-all-read` | Mark all alerts read | Yes |
| GET | `/api/v2/network/stats/dashboard` | Get network stats | Yes |

### Payments
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v2/payments/plans` | List payment plans | Yes |
| POST | `/api/v2/payments/intent` | Create payment intent | Yes |
| POST | `/api/v2/payments/subscribe` | Subscribe to plan | Yes |
| POST | `/api/v2/payments/webhook` | Culqi webhook handler | No |

### Dashboard
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/dashboard/stats` | Get dashboard stats | Yes |
| GET | `/api/v1/dashboard/metrics` | Get detailed metrics | Yes |

### Admin
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/admin/companies` | List all companies | Admin |
| GET | `/api/v1/admin/applications` | List founder applications | Admin |
| POST | `/api/v1/admin/applications/{id}/approve` | Approve application | Admin |
| POST | `/api/v1/admin/applications/{id}/reject` | Reject application | Admin |

### Webhooks
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/webhooks` | List webhooks | Yes |
| POST | `/api/v1/webhooks` | Create webhook | Yes |
| DELETE | `/api/v1/webhooks/{id}` | Delete webhook | Yes |
| POST | `/api/v1/webhooks/{id}/test` | Test webhook | Yes |

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input data |
| 401 | Unauthorized - Invalid or missing token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

## Rate Limits

- Authentication endpoints: 5 requests per minute
- Verification endpoints: 10 requests per minute
- General API endpoints: 60 requests per minute
- Webhook endpoints: 100 requests per minute

## Response Format

All responses follow this structure:
```json
{
  "success": true,
  "data": { ... },
  "message": "Optional message"
}
```

Error responses:
```json
{
  "success": false,
  "error": "Error type",
  "detail": "Detailed error message"
}
```

## Scoring System

The risk score is calculated on a scale of 0-100:

| Score | Level | Color | Description |
|-------|-------|-------|-------------|
| 80-100 | Bajo Riesgo | Green | Low risk, reliable supplier |
| 60-79 | Riesgo Medio | Orange | Medium risk, some concerns |
| 40-59 | Alto Riesgo | Red | High risk, significant issues |
| 0-39 | Riesgo Crítico | Dark Red | Critical risk, avoid |

## Versioning

The API uses URL versioning:
- `/api/v1/` - Original endpoints (stable)
- `/api/v2/` - New endpoints (current)

Both versions are maintained for backward compatibility.

## Webhooks

Webhooks are sent as POST requests to your configured URL with the following headers:
```
X-Webhook-Signature: <hmac_signature>
Content-Type: application/json
```

Event types:
- `verification.completed` - Verification finished
- `supplier.score_changed` - Supplier score changed
- `supplier.new_sanction` - New sanction detected
- `payment.success` - Payment successful
- `payment.failed` - Payment failed

## SDKs & Libraries

### Python
```python
import requests

api = requests.Session()
api.headers.update({
    "Authorization": "Bearer YOUR_TOKEN"
})

# Verify a RUC
response = api.post("https://api.conflictzero.com/api/v1/verify", json={"ruc": "20100101K01"})
data = response.json()
```

### JavaScript
```javascript
const api = axios.create({
  baseURL: 'https://api.conflictzero.com',
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN'
  }
});

// Verify a RUC
const { data } = await api.post('/api/v1/verify', { ruc: '20100101K01' });
```

## Support

For API support, contact:
- Email: api-support@conflictzero.com
- Documentation: https://docs.conflictzero.com
- Status: https://status.conflictzero.com

---

*API Version: 2.0.0*
*Last Updated: 2026-04-23*

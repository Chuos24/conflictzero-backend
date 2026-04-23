# Conflict Zero - Architecture Documentation

## Overview

Conflict Zero is a supplier risk verification system for Peruvian companies. It provides:
- RUC verification against SUNAT/OSCE/TCE databases
- Risk scoring (0-100 scale)
- Digital certificates with QR codes
- Supplier network monitoring
- Payment processing (Culqi integration)

## System Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Landing Page  │     │    Dashboard    │     │   Founder App   │
│   (HTML/CSS)    │     │  (React + Vite) │     │  (React + Vite) │
│   :3000         │     │    :5173        │     │    :3001        │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │     Nginx (Reverse      │
                    │        Proxy)           │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │    FastAPI Backend      │
                    │       (Python)          │
                    │        :8000            │
                    └────────────┬────────────┘
                                 │
           ┌─────────────────────┼─────────────────────┐
           │                     │                     │
    ┌──────▼──────┐    ┌─────────▼─────────┐   ┌────▼────┐
    │  PostgreSQL │    │      Redis        │   │  Static │
    │    :5432    │    │      :6379        │   │  Files  │
    └─────────────┘    └───────────────────┘   └─────────┘
```

## Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11)
- **ORM**: SQLAlchemy 2.0
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Authentication**: JWT + bcrypt
- **Validation**: Pydantic v2
- **Rate Limiting**: Redis-based sliding window
- **PDF Generation**: ReportLab + pyhanko (for digital signatures)
- **Email**: SendGrid
- **Payments**: Culqi API v2

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite 5
- **Router**: React Router DOM v6
- **Charts**: Recharts
- **HTTP Client**: Axios
- **Styling**: CSS Modules + Global CSS
- **State Management**: React Context API

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Reverse Proxy**: Nginx
- **CI/CD**: GitHub Actions
- **Hosting**: Render.com (Blueprints)
- **Database**: Render PostgreSQL
- **Cache**: Render Redis

## Data Flow

### Verification Flow
```
1. User submits RUC
2. Backend validates RUC format
3. Check cache (Redis)
4. If not cached:
   a. Query local database
   b. Query external APIs (SUNAT/OSCE/TCE)
   c. Calculate risk score
   d. Store in database
   e. Cache result (1 hour)
5. Return verification result
6. Generate certificate (PDF with QR)
```

### Payment Flow
```
1. User selects plan
2. Backend creates payment intent (Culqi)
3. Frontend shows Culqi checkout
4. User enters card details
5. Culqi processes payment
6. Webhook confirms payment
7. Backend updates subscription
8. User gets confirmation
```

### Supplier Network Monitoring
```
1. User adds supplier to network
2. System stores supplier RUC (hashed)
3. Daily cron job:
   a. Re-verify all suppliers
   b. Compare with previous scores
   c. Generate alerts if changes detected
4. User receives notifications
```

## Database Schema

### Core Tables

#### companies
- Primary table for registered companies
- Stores: id, ruc_encrypted, company_name, legal_name, email, plan_tier
- Indexes: ruc_hash (for lookups), email, plan_tier

#### verification_requests
- Stores verification history
- Stores: id, company_id, ruc_hash, status, score, result_data
- Indexes: company_id, created_at

#### invites
- Invitation system for network building
- Stores: id, inviter_id, email, status, token
- Indexes: token (unique), email, inviter_id

#### founder_applications
- Founder program applications
- Stores: id, company_id, status, application_data
- Indexes: company_id, status

#### compliance_checks
- Compliance tracking for founders
- Stores: id, company_id, check_type, status, due_date
- Indexes: company_id, due_date, status

#### api_keys
- API key management
- Stores: id, company_id, key_hash, name, permissions
- Indexes: key_hash (unique), company_id

#### webhooks
- Webhook configurations
- Stores: id, company_id, url, events, secret
- Indexes: company_id

#### audit_logs
- System audit trail
- Stores: id, company_id, action, details, ip_address
- Indexes: company_id, created_at

### Network Tables

#### supplier_networks
- Supplier network relationships
- Stores: id, company_id, supplier_ruc_hash, supplier_company_name, is_active
- Indexes: company_id, supplier_ruc_hash

#### supplier_alerts
- Alerts for supplier changes
- Stores: id, network_id, alert_type, severity, message
- Indexes: network_id, created_at, is_read

#### company_snapshots
- Historical snapshots for trend analysis
- Stores: id, company_id, score, debt_data, sanction_data
- Indexes: company_id, created_at

## Security

### Authentication
- JWT tokens with 24-hour expiration
- Refresh tokens with 7-day expiration
- Password hashing with bcrypt (12 rounds)

### Authorization
- Role-based access control (RBAC)
- Admin endpoints require admin role
- API keys with scoped permissions

### Data Protection
- RUC encryption at rest (AES-256)
- RUC hashing for lookups (SHA-256)
- TLS 1.3 for all communications

### Rate Limiting
- Sliding window algorithm
- Per-endpoint limits
- Redis-backed counters

## Caching Strategy

### Redis Usage
1. **Verification Cache**: 1 hour TTL
2. **Session Store**: 24 hour TTL
3. **Rate Limit Counters**: 1 minute TTL
4. **Dashboard Stats**: 5 minute TTL
5. **API Response Cache**: 10 minute TTL

### Cache Invalidation
- Time-based expiration (TTL)
- Event-based invalidation (on updates)
- Manual purge (admin endpoint)

## Scalability

### Horizontal Scaling
- Stateless backend design
- Shared Redis for sessions/cache
- PostgreSQL with read replicas

### Performance Optimizations
- Database connection pooling
- Query optimization with indexes
- Async endpoints for I/O operations
- Background tasks for heavy operations

## Monitoring

### Health Checks
- `/health` - Basic health check
- `/api/v2/status` - Detailed status with dependencies

### Metrics
- Request latency (X-Process-Time header)
- Error rates
- Cache hit/miss ratios
- Database query performance

### Alerts
- Webhook delivery failures
- Payment processing errors
- Supplier score changes
- Compliance deadline reminders

## Deployment

### Local Development
```bash
docker-compose up -d
```
Services:
- PostgreSQL: localhost:5432
- Redis: localhost:6379
- Backend: localhost:8000
- Dashboard: localhost:5173

### Production (Render.com)
1. Push to GitHub
2. Render Blueprint creates:
   - PostgreSQL database
   - Redis instance
   - Backend service
   - Dashboard static site
3. Run migrations: `alembic upgrade head`
4. Configure environment variables

## Environment Variables

### Backend
```env
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
SECRET_KEY=your-secret-key
ENCRYPTION_KEY=your-32-char-key
CULQI_PUBLIC_KEY=pk_test_...
CULQI_SECRET_KEY=sk_test_...
SENDGRID_API_KEY=SG.xxx
ENVIRONMENT=production
DEBUG=false
```

### Dashboard
```env
VITE_API_URL=https://api.conflictzero.com
```

## Future Improvements

1. **Microservices**: Split into verification, payments, notifications services
2. **GraphQL**: Add GraphQL API alongside REST
3. **Real-time**: WebSocket notifications for alerts
4. **ML Scoring**: Machine learning risk prediction
5. **Mobile App**: React Native mobile application
6. **Multi-region**: Deploy in multiple regions for latency

---

*Architecture Version: 2.0*
*Last Updated: 2026-04-23*

# Conflict Zero - Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability, please send an email to security@czperu.com with:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We will respond within 48 hours and work to resolve the issue promptly.

## Security Measures

### Data Protection

- **RUC Encryption:** All RUCs are encrypted at rest using AES-256
- **Password Hashing:** bcrypt with salt rounds 12+
- **HTTPS Only:** All communications use TLS 1.3
- **Database:** PostgreSQL with SSL connections

### Access Control

- JWT tokens with short expiration (1 hour)
- API keys with granular scopes
- Rate limiting per user/API key
- IP-based restrictions available

### Compliance

- GDPR compliant (soft delete + data retention)
- INDECOPI certified digital signatures
- 5-year data retention for legal compliance
- Audit logs for all operations

### Secrets Management

Required environment variables:

```bash
SECRET_KEY=<generate with openssl rand -hex 32>
DATABASE_URL=<postgresql with ssl>
INDECOPI_CERT_PASSWORD=<protected>
SENDGRID_API_KEY=<optional>
```

Never commit secrets to the repository.

## Security Checklist for Deployment

- [ ] Change default SECRET_KEY
- [ ] Enable HTTPS only
- [ ] Configure CORS properly
- [ ] Set up rate limiting
- [ ] Enable audit logging
- [ ] Configure backup encryption
- [ ] Set up monitoring/alerting
- [ ] Review access controls

## Contact

security@czperu.com

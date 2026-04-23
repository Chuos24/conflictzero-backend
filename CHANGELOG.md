# Changelog

All notable changes to Conflict Zero will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-04-23

### Added
- Fase 1.5: Supplier Network (Mi Red) module
- Network monitoring with alerts
- Payment processing with Culqi integration
- Founder program compliance tracking
- Daily cron job for network checks
- Admin dashboard endpoints
- 40 tests (100% passing)

### Changed
- Improved error handling across all routers
- Enhanced rate limiting with Redis
- Updated authentication middleware

### Fixed
- Frontend build imports (named vs default exports)
- Founder applications nullable RUC field
- SQLite-incompatible queries in compliance stats

## [1.5.0] - 2026-04-18

### Added
- Supplier network management
- Alert system for supplier changes
- Company snapshots for trend analysis
- Network dashboard stats

### Changed
- Refactored database models for network tables
- Updated API client with network endpoints

## [1.0.0] - 2026-04-11

### Added
- Initial release of Conflict Zero Fase 1
- FastAPI backend with 45+ endpoints
- React 18 dashboard with 8 pages
- Landing page
- Docker Compose infrastructure
- CI/CD pipeline with GitHub Actions
- JWT authentication
- RUC verification system
- Risk scoring (0-100)
- Digital certificates with QR codes
- Company comparison (up to 10 RUCs)
- Invitation system
- Webhook support
- 23 tests (unit + integration)

### Security
- AES-256 encryption for RUC storage
- SHA-256 hashing for RUC lookups
- JWT token authentication
- Rate limiting
- Input validation with Pydantic

---

## Release Checklist

- [ ] Update version in `backend/app/main.py`
- [ ] Update version in `dashboard/package.json`
- [ ] Update `CHANGELOG.md`
- [ ] Run all tests
- [ ] Update API documentation
- [ ] Update architecture documentation
- [ ] Create Git tag
- [ ] Deploy to staging
- [ ] Deploy to production

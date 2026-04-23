# Contributing to Conflict Zero

Thank you for your interest in contributing to Conflict Zero! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker and Docker Compose
- Git

### Quick Start

1. Clone the repository:
```bash
git clone https://github.com/your-org/conflict-zero.git
cd conflict-zero
```

2. Start the infrastructure:
```bash
docker-compose up -d
```

3. Set up the backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

4. Set up the dashboard:
```bash
cd dashboard
npm install
```

5. Run the development server:
```bash
# Terminal 1 - Backend
cd backend
uvicorn app.main:app --reload

# Terminal 2 - Dashboard
cd dashboard
npm run dev
```

## Project Structure

```
conflict-zero/
├── backend/           # FastAPI application
│   ├── app/          # Main application code
│   ├── tests/        # Test files
│   ├── alembic/      # Database migrations
│   └── scripts/      # Utility scripts
├── dashboard/        # React frontend
│   ├── src/         # Source code
│   └── public/      # Static assets
├── landing/         # Landing page
├── docs/            # Documentation
└── docker-compose.yml
```

## Coding Standards

### Python (Backend)
- Follow PEP 8
- Use type hints
- Write docstrings for all functions/classes
- Keep functions focused and small
- Use SQLAlchemy 2.0 style queries

### JavaScript/React (Frontend)
- Use functional components
- Use hooks for state management
- Follow React best practices
- Use CSS modules for component styles

## Testing

### Running Tests

```bash
# Backend tests
cd backend
pytest -v

# Specific test categories
pytest -m unit       # Unit tests only
pytest -m integration # Integration tests only

# With coverage
pytest --cov=app --cov-report=html
```

### Writing Tests
- Write tests for all new features
- Use descriptive test names
- Mock external API calls
- Test both success and error cases

## Pull Request Process

1. Create a feature branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes
3. Write or update tests
4. Update documentation
5. Run all tests
6. Commit your changes:
```bash
git add .
git commit -m "feat: add new feature description"
```

7. Push to your fork:
```bash
git push origin feature/your-feature-name
```

8. Create a Pull Request

### Commit Message Format
Follow conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting)
- `refactor:` Code refactoring
- `test:` Test changes
- `chore:` Maintenance tasks

Example:
```
feat: add supplier network alerts

- Add alert model and schema
- Implement alert CRUD endpoints
- Add tests for alert functionality
```

## Code Review

All submissions require review. We use GitHub pull requests for this purpose.

### Review Checklist
- [ ] Code follows style guidelines
- [ ] Tests are included
- [ ] Documentation is updated
- [ ] No security vulnerabilities
- [ ] Performance is acceptable

## Database Migrations

When modifying database models:

1. Update the model in `backend/app/models_v2.py`
2. Generate migration:
```bash
cd backend
alembic revision --autogenerate -m "description"
```
3. Review the generated migration
4. Apply migration:
```bash
alembic upgrade head
```

## Environment Variables

Never commit sensitive values:
- Keep `.env` in `.gitignore`
- Use `.env.example` for documentation
- Use strong secrets in production

## Questions?

- Open an issue for bugs
- Start a discussion for questions
- Contact the team at dev@conflictzero.com

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to Conflict Zero! 🚀

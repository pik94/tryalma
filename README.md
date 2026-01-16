# Lead Management Service

A FastAPI-based service for managing legal leads and attorney assignments. The service provides REST APIs for lead management, automated email outreach, and attorney workload distribution.

## Features

### Core Functionality
- **Lead Management**: Create, retrieve, and update legal leads with resume attachments
- **Attorney Management**: Track attorney availability and workload distribution
- **Automated Email Outreach**: Background task system for sending emails to registered leads
- **Status Tracking**: Monitor lead progression through different stages (registered, reached_out, etc.)
- **Health Monitoring**: Built-in health check endpoints for service monitoring

### API Endpoints
- `POST /api/v1/leads` - Create new lead with resume upload
- `GET /api/v1/leads` - Retrieve paginated list of leads (authenticated)
- `GET /api/v1/leads/{lead_id}` - Get specific lead details (authenticated)
- `PATCH /api/v1/leads/{lead_id}` - Update lead status and assignment (authenticated)
- `GET /api/v1/healthcheck` - Service health status

### Background Tasks
- **Email Automation**: Automatically sends welcome emails to registered leads
- **Attorney Assignment**: Assigns least busy attorney to each lead
- **Status Updates**: Updates lead status to 'reached_out' after successful email delivery

## Architecture

### Tech Stack
- **Framework**: FastAPI with async/await support
- **Database**: PostgreSQL with SQLAlchemy ORM and Alembic migrations
- **Authentication**: JWT-based authentication
- **Task Scheduling**: APScheduler for background tasks
- **Testing**: Pytest with async support and comprehensive fixtures
- **Code Quality**: Ruff for linting and formatting

### Project Structure
```
service/
├── api/v1/              # REST API endpoints
│   ├── leads/           # Lead management endpoints
│   └── healthcheck/     # Health monitoring
├── database/            # Database models and migrations
│   ├── models/          # SQLModel database models
│   └── mixins/          # Reusable model mixins
├── services/            # Business logic services
│   ├── leads/           # Lead management service
│   ├── attorneys/       # Attorney management service
│   ├── email_service/   # Email sending service
│   └── blob_storage/    # File storage service
├── tasks/               # Background task definitions
├── settings/            # Configuration management
└── utils/               # Utility functions
```

## Development Setup

### Prerequisites
- Python 3.12+
- PostgreSQL
- Docker & Docker Compose (optional)

### Local Development
1. **Start development stack**
   ```bash
   make dev-stack-run
   ```

2. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

3. **Install dependencies**
   ```bash
   uv sync
   ```

4. **Run the web application**
   ```bash
   PYTHONPATH=. uv run python service/web_app.py
   ```

5. **Run the scheduler (background tasks)**
   ```bash
   PYTHONPATH=. uv run python service/scheduler.py
   ```

### Docker Development
Run all services in Docker:
```bash
make PROFILE=dev-app dev-stack-up
```

## Testing

### Run Tests
1. **Start test stack**
   ```bash
   make test-stack-up
   ```

2. **Execute tests**
   ```bash
   source .venv/bin/activate && pytest
   ```

### Test Coverage
The service includes comprehensive test coverage for:
- **API Endpoints**: All REST endpoints with authentication scenarios
- **Background Tasks**: Email automation and error handling
- **Database Operations**: CRUD operations with fixtures
- **Service Layer**: Business logic and error scenarios

### Test Structure
- `tests/api/` - API endpoint tests
- `tests/database/` - Database model and fixture tests  
- `tests/services/` - Business logic service tests
- `tests/tasks/` - Background task tests

## Configuration

The service uses environment-based configuration with the following key settings:

### Environment Files
- `configs/.env.dev` - Development environment
- `configs/.env.test` - Test environment
- `configs/overrides/` - Environment-specific overrides

### Key Configuration Areas
- **Database**: Connection strings and pool settings
- **Authentication**: JWT secrets and token expiration
- **Email Service**: SMTP configuration for outreach
- **Scheduler**: Background task intervals and settings
- **Blob Storage**: File upload and storage configuration

## API Usage Examples

### Create a Lead
```bash
curl -X POST "http://localhost:8000/api/v1/leads" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe", 
    "email": "john.doe@example.com",
    "resume": "base64_encoded_resume_data"
  }'
```

### Get Leads (Authenticated)
```bash
curl -X GET "http://localhost:8000/api/v1/leads?limit=10&offset=0" \
  -H "Authorization: Bearer your_jwt_token"
```

### Update Lead Status (Authenticated)
```bash
curl -X PATCH "http://localhost:8000/api/v1/leads/{lead_id}" \
  -H "Authorization: Bearer your_jwt_token" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "reached_out",
    "reached_out_by": "attorney_uuid"
  }'
```
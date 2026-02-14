# RentBnB - Multi-Tenant Property Rental Management System

A modern, scalable backend for a property rental management platform built with FastAPI, PostgreSQL, and Redis.

## Features

- **Multi-Tenant Architecture**: Complete tenant isolation with role-based access control
- **User Authentication**: JWT-based authentication with refresh tokens and passwordless OTP login
- **Email Verification**: Automated email-based account verification
- **Password Management**: Secure password hashing with bcrypt, forgot password/reset flow
- **Property Management**: Complete property lifecycle management with amenities and images
- **Booking System**: Full booking lifecycle management with availability checks and status tracking
- **Payment Integration**: Secure payments via Razorpay with refund handling and webhook support
- **Real-time Messaging**: WebSocket-based chat system for instant communication
- **Background Processes**: Asynchronous task processing using Celery (emails, refunds)
- **Image Handling**: Secure image uploads with UUID filenames and static file serving
- **Role-Based Access Control**: Support for SUPER_ADMIN, TENANT_ADMIN, MANAGER, and GUEST roles
- **Database Migrations**: Automated schema versioning with Alembic
- **Caching Layer**: Redis integration for OTP, verification tokens, and temporary data
- **Email Notifications**: SMTP-based email support for verification and password reset
- **CORS Support**: Configured for frontend integration
- **Exception Handling**: Comprehensive error handling and validation
- **Async Operations**: Full async/await support for high performance

## Tech Stack

- **Framework**: FastAPI 0.128+
- **Database**: PostgreSQL with async support (asyncpg)
- **Cache**: Redis 7.1+
- **Task Queue**: Celery 5.3+
- **Payment Gateway**: Razorpay
- **Authentication**: JWT with bcrypt password hashing
- **ORM**: SQLAlchemy 2.0+
- **Migrations**: Alembic 1.18+
- **Email**: aiosmtplib for async email
- **Python**: 3.13+

## Prerequisites

- Python 3.13 or higher
- PostgreSQL 12+
- Redis 6.0+
- Git

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd rentbnb
   ```

2. **Create virtual environment** (if not already created)
   ```bash
   python -m venv .venv
   source .venv/bin/activate 
   ```

3. **Install dependencies**
   ```bash
   uv install
   ```
   Or with pip:
   ```bash
   pip install -e .
   ```

## Environment Setup

1. **Copy environment template**
   ```bash
   cp .env.example .env
   ```

2. **Configure `.env` file**
   ```env
   # Database
   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/rentbnb

   # Auth
   SECRET_KEY=your-secret-key-min-32-characters-long-change-this-in-production
   ALGORITHM=HS256
   ACCESS_EXPIRE_MIN=15
   REFRESH_EXPIRE_DAYS=7

   # Redis
   REDIS_URL=redis://localhost:6379/0

   # CORS Origins
   CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]

   # Frontend
   FRONTEND_URL=http://localhost:3000

   # Email (SMTP)
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   EMAILS_FROM_EMAIL=noreply@rentbnb.com
   EMAILS_FROM_NAME=RentBnB

   # Payments (Razorpay)
   RAZORPAY_KEY_ID=rzp_test_...
   RAZORPAY_KEY_SECRET=your-secret-key
   RAZORPAY_WEBHOOK_SECRET=your-webhook-secret

   # Development
   DEBUG=false
   ```

## Database Setup

1. **Ensure PostgreSQL is running**
   ```bash
   # macOS with Homebrew
   brew services start postgresql

   # Or start manually
   postgres -D /usr/local/var/postgres
   ```

2. **Create database**
   ```bash
   createdb rentbnb
   ```

3. **Run migrations**
   ```bash
   alembic upgrade head
   ```

## Running the Application

1. **Ensure Redis is running**
   ```bash
   redis-server
   ```

2. **Start the API server**
   ```bash
   uvicorn app.main:app --reload
   ```

   The API will be available at `http://localhost:8000`

3. **Start Celery Worker** (for background tasks)
   ```bash
   celery -A app.celery_app worker --loglevel=info
   ```

4. **Start Celery Beat** (for scheduled tasks)
   ```bash
   celery -A app.celery_app beat --loglevel=info
   ```

5. **Access interactive API documentation**
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

## Project Structure

```
rentbnb/
├── app/
│   ├── config/          # Configuration and settings
│   ├── constants/       # Application constants and enums
│   ├── crud/            # Database CRUD operations
│   ├── database/        # Database connection and session management
│   ├── dependencies/    # FastAPI dependency injection
│   ├── enums/           # Enum definitions
│   ├── models/          # SQLAlchemy ORM models
│   ├── routers/         # API route handlers
│   │   ├── auth.py      # Authentication endpoints
│   │   ├── tenant.py    # Tenant management endpoints
│   │   └── user.py      # User management endpoints
│   ├── schemas/         # Pydantic request/response schemas
│   ├── services/        # Business logic layer
│   ├── utils/           # Utility functions and helpers
│   └── main.py          # FastAPI application entry point
├── migrations/          # Alembic database migrations
├── scripts/             # Utility scripts
├── .env.example         # Environment variables template
├── alembic.ini          # Alembic configuration
└── pyproject.toml       # Project metadata and dependencies
```

## Authentication & Security

### User Roles
- **SUPER_ADMIN**: Can manage all tenants and users system-wide
- **TENANT_ADMIN**: Manages their tenant and its users
- **MANAGER**: Works within their tenant (limited permissions)
- **GUEST**: View-only access within tenant

### Authentication Methods
- **Email & Password**: Traditional login with JWT tokens
- **Passwordless OTP**: One-time password sent to email
- **Token Refresh**: Long-lived refresh tokens for extended sessions
- **Email Verification**: Required for new accounts
- **Password Reset**: Secure password reset via email token

### Security Features
- Bcrypt password hashing
- JWT token-based authentication
- Soft-delete pattern for data retention
- Token blacklisting on logout
- Case-insensitive email/username lookups
- Role-based access control (RBAC)
- Multi-tenant isolation at database level

## Development

### Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback last migration:
```bash
alembic downgrade -1
```

# RentBnB - Multi-Tenant Property Rental Management System

A modern, scalable backend for a property rental management platform built with FastAPI, PostgreSQL, and Redis.

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
   
   Scheduled tasks:
   - **Payment Reconciliation**: Runs every 2 minutes to check pending payments
   - **Token Cleanup**: Runs every 6 hours to remove expired tokens

5. **Access interactive API documentation**
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

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


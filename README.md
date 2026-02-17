# RentBnB - Multi-Tenant Property Rental Management System

A modern, scalable backend for a property rental management platform built with FastAPI, PostgreSQL, and Redis.

## Features

### Core Architecture
- **Multi-Tenant Architecture**: Complete tenant isolation with role-based access control and tenant-scoped data
- **Role-Based Access Control**: Support for SUPER_ADMIN, TENANT_ADMIN, MANAGER, and GUEST roles
- **Async Operations**: Full async/await support for high performance
- **Database Migrations**: Automated schema versioning with Alembic
- **Exception Handling**: Comprehensive error handling and validation with custom exception handlers
- **CORS Support**: Configured for frontend integration

### Authentication & Security
- **JWT Authentication**: Token-based authentication with access and refresh tokens
- **Passwordless OTP**: One-time password login sent via email
- **Email Verification**: Automated email-based account verification
- **Password Management**: Secure password hashing with bcrypt, forgot password/reset flow
- **Token Management**: Automatic token cleanup via scheduled tasks (every 6 hours)
- **Rate Limiting**: Intelligent IP-based rate limiting for sensitive endpoints (Auth, OTP) using Redis atomic counters
- **Soft Delete Pattern**: Data retention with soft-delete for users, tenants, and other entities

### Property & Amenity Management
- **Property Management**: Complete CRUD operations for properties with multi-image support
- **Property Images**: Secure image uploads with UUID filenames and static file serving
- **Amenity System**: Manage property amenities with tenant-specific amenity catalogs
- **Property Categories**: Support for APARTMENT, HOUSE, VILLA, CONDO, etc.
- **Availability Tracking**: Real-time property availability checks

### Booking & Payment System
- **Booking System**: Full booking lifecycle management with status tracking (PENDING, CONFIRMED, CANCELLED, FAILED)
- **Availability Checks**: Prevent double-bookings with date range validation
- **Payment Integration**: Razorpay payment gateway with order creation and verification
- **Refund Processing**: Automated refund handling via Celery tasks
- **Payment Webhooks**: Real-time payment status updates via Razorpay webhooks
- **Payment Reconciliation**: Scheduled task to reconcile pending payments (every 2 minutes)

### Reviews & Ratings
- **Review System**: Guests can review properties after completed bookings
- **Rating Management**: 1-5 star ratings with review text
- **Review Validation**: Ensures only guests with completed bookings can review
- **Tenant Isolation**: Reviews are tenant-scoped

### Messaging & Real-time Communication
- **WebSocket Support**: Real-time bidirectional communication
- **Message System**: Persistent message storage with sender tracking
- **Message Types**: Support for TEXT message types
- **Real-time Notifications**: Instant message delivery via WebSockets

### Dashboard & Analytics
- **Tenant Dashboard**: Metrics for tenant admins (total properties, bookings, revenue, occupancy rate)
- **Platform Dashboard**: System-wide metrics for super admins (total tenants, users, properties, bookings, revenue)
- **Date Range Filtering**: Dashboard metrics support custom date ranges
- **Performance Optimized**: Database indexes for efficient metric aggregation

### Background Processing
- **Celery Worker**: Asynchronous task processing for emails, refunds, and bookings
- **Celery Beat**: Scheduled tasks for payment reconciliation and token cleanup
- **Email Tasks**: Async email sending for verification, password reset, and notifications
- **Booking Tasks**: Automated booking expiration handling
- **Payment Tasks**: Refund processing and payment reconciliation

### Caching & Storage
- **Redis Integration**: Caching for OTP, verification tokens, and session data
- **Static File Serving**: Dedicated endpoints for uploaded images and static assets
- **File Upload Handling**: Secure multipart file uploads with validation
- **Rate Limiting**: Custom Redis-based rate limiter with atomic counters to prevent abuse (IP-based tracking)

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

## API Endpoints

All API endpoints are prefixed with `/api/v1`.

### Authentication (`/auth`)
- `POST /register` - Register new user (requires `x-tenant-id` header)
- `POST /login` - Login with email/password
- `POST /refresh` - Refresh access token
- `POST /logout` - Logout and invalidate tokens
- `POST /verify-email` - Verify email with token
- `POST /resend-verification` - Resend verification email
- `POST /forgot-password` - Request password reset
- `POST /reset-password` - Reset password with token
- `POST /otp/request` - Request OTP for passwordless login
- `POST /otp/verify` - Verify OTP and login

### Users (`/users`)
- `GET /me` - Get current user profile
- `PUT /me` - Update current user profile
- `DELETE /me` - Soft delete current user
- `GET /` - List users (admin only)
- `GET /{user_id}` - Get user by ID (admin only)
- `PUT /{user_id}` - Update user (admin only)
- `DELETE /{user_id}` - Delete user (admin only)

### Tenants (`/tenants`)
- `POST /` - Create new tenant (super admin only)
- `GET /` - List all tenants (super admin only)
- `GET /{tenant_id}` - Get tenant details
- `PUT /{tenant_id}` - Update tenant
- `DELETE /{tenant_id}` - Soft delete tenant (super admin only)

### Properties (`/properties`)
- `POST /` - Create new property
- `GET /` - List properties (with pagination and filters)
- `GET /{property_id}` - Get property details
- `PUT /{property_id}` - Update property
- `DELETE /{property_id}` - Soft delete property
- `POST /{property_id}/images` - Upload property images
- `DELETE /{property_id}/images/{image_id}` - Delete property image

### Amenities (`/amenities`)
- `POST /` - Create amenity
- `GET /` - List amenities
- `GET /{amenity_id}` - Get amenity details
- `PUT /{amenity_id}` - Update amenity
- `DELETE /{amenity_id}` - Soft delete amenity

### Bookings (`/bookings`)
- `POST /` - Create new booking
- `GET /` - List bookings (with filters)
- `GET /{booking_id}` - Get booking details
- `PUT /{booking_id}` - Update booking
- `DELETE /{booking_id}` - Cancel booking
- `POST /{booking_id}/confirm` - Confirm booking

### Payments (`/payments`)
- `POST /create-order` - Create Razorpay payment order
- `POST /verify` - Verify payment signature
- `GET /` - List payments
- `GET /{payment_id}` - Get payment details
- `POST /webhook` - Razorpay webhook handler

### Reviews (`/reviews`)
- `POST /` - Create review (guests only, after completed booking)
- `GET /` - List reviews
- `GET /{review_id}` - Get review details
- `PUT /{review_id}` - Update review
- `DELETE /{review_id}` - Delete review
- `GET /property/{property_id}` - Get reviews for a property

### Messages (`/messages`)
- `POST /` - Send message
- `GET /` - List messages (with pagination)
- `GET /{message_id}` - Get message details
- `GET /conversation/{user_id}` - Get conversation with specific user

### Dashboard (`/dashboard`)
- `GET /tenant` - Get tenant dashboard metrics (admin only)
- `GET /platform` - Get platform-wide metrics (super admin only)

### WebSocket (`/ws`)
- `WS /{user_id}` - WebSocket connection for real-time messaging


## Project Structure

```
rentbnb/
├── app/
│   ├── config/          # Configuration and settings
│   ├── constants/       # Application constants and enums
│   ├── crud/            # Database CRUD operations
│   ├── database/        # Database connection and session management
│   ├── dependencies/    # FastAPI dependency injection
│   ├── enums/           # Enum definitions (roles, statuses, categories)
│   ├── models/          # SQLAlchemy ORM models
│   │   ├── amenity.py
│   │   ├── booking.py
│   │   ├── message.py
│   │   ├── payment.py
│   │   ├── property.py
│   │   ├── property_image.py
│   │   ├── review.py
│   │   ├── tenant.py
│   │   ├── user.py
│   │   └── webhook.py
│   ├── routers/         # API route handlers
│   │   ├── amenity.py      # Amenity management endpoints
│   │   ├── auth.py         # Authentication endpoints
│   │   ├── booking.py      # Booking management endpoints
│   │   ├── dashboard.py    # Dashboard analytics endpoints
│   │   ├── message.py      # Messaging endpoints
│   │   ├── payment.py      # Payment processing endpoints
│   │   ├── property.py     # Property management endpoints
│   │   ├── review.py       # Review and rating endpoints
│   │   ├── tenant.py       # Tenant management endpoints
│   │   ├── user.py         # User management endpoints
│   │   └── websocket.py    # WebSocket connection handler
│   ├── schemas/         # Pydantic request/response schemas
│   ├── services/        # Business logic layer
│   │   ├── auth_service.py
│   │   ├── booking_service.py
│   │   ├── dashboard_service.py
│   │   ├── email_service.py
│   │   ├── message_service.py
│   │   ├── payment_service.py
│   │   ├── property_service.py
│   │   ├── review_service.py
│   │   ├── tenant_service.py
│   │   └── user_service.py
│   ├── tasks/           # Celery background tasks
│   │   ├── auth_tasks.py     # Token cleanup tasks
│   │   ├── booking_tasks.py  # Booking expiration tasks
│   │   ├── email_tasks.py    # Email sending tasks
│   │   └── payment_tasks.py  # Payment reconciliation and refund tasks
│   ├── utils/           # Utility functions and helpers
│   ├── celery_app.py    # Celery configuration and beat schedule
│   └── main.py          # FastAPI application entry point
├── migrations/          # Alembic database migrations
├── scripts/             # Utility scripts
├── static/              # Static files directory
├── uploads/             # User-uploaded files (property images)
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

## Role-Based Permission Matrix

This matrix defines what each role can do across all modules in the system. All permissions are tenant-scoped unless explicitly marked as "Global" (system-wide).

### Legend
- **Yes** - Full access to this operation
- **Own** - Can only access their own resources
- **Tenant** - Can access all resources within their tenant
- **No** - No access to this operation
- **Global** - System-wide access across all tenants

---

### Tenant Management

| Operation | SUPER_ADMIN | TENANT_ADMIN | MANAGER | GUEST |
|-----------|-------------|--------------|---------|-------|
| Create Tenant | Yes (Global) | No | No | No |
| List All Tenants | Yes (Global) | No | No | No |
| View Tenant Details | Yes (Global) | Yes (Own) | Yes (Own) | Yes (Own) |
| Update Tenant | Yes (Global) | Yes (Own) | No | No |
| Delete Tenant | Yes (Global) | No | No | No |

---

### User Management

| Operation | SUPER_ADMIN | TENANT_ADMIN | MANAGER | GUEST |
|-----------|-------------|--------------|---------|-------|
| Register User | Yes | Yes | Yes | Yes |
| List Users | Yes (Global) | Yes (Tenant) | No | No |
| View User Profile (Own) | Yes | Yes | Yes | Yes |
| View User Profile (Others) | Yes (Global) | Yes (Tenant) | No | No |
| Update User (Own) | Yes | Yes | Yes | Yes |
| Update User (Others) | Yes (Global) | Yes (Tenant) | No | No |
| Delete User (Own) | Yes | Yes | Yes | Yes |
| Delete User (Others) | Yes (Global) | Yes (Tenant) | No | No |
| Change User Role | Yes (Global) | Yes (Tenant) | No | No |

---

### Property Management

| Operation | SUPER_ADMIN | TENANT_ADMIN | MANAGER | GUEST |
|-----------|-------------|--------------|---------|-------|
| Create Property | No | Yes (Tenant) | Yes (Tenant) | No |
| List Properties | No | Yes (Tenant) | Yes (Tenant) | Yes (Tenant) |
| View Property Details | No | Yes (Tenant) | Yes (Tenant) | Yes (Tenant) |
| Update Property | No | Yes (Tenant) | Yes (Tenant) | No |
| Delete Property | No | Yes (Tenant) | Yes (Tenant) | No |
| Upload Property Images | No | Yes (Tenant) | Yes (Tenant) | No |
| Delete Property Images | No | Yes (Tenant) | Yes (Tenant) | No |

> **Note**: SUPER_ADMIN does not have access to property management. This is tenant-scoped functionality managed by TENANT_ADMIN and MANAGER roles only.

---

### Amenity Management

| Operation | SUPER_ADMIN | TENANT_ADMIN | MANAGER | GUEST |
|-----------|-------------|--------------|---------|-------|
| Create Amenity | Yes (Global) | No | No | No |
| List Amenities | Yes | Yes | Yes | Yes |
| View Amenity Details | Yes | Yes | Yes | Yes |
| Update Amenity | Yes (Global) | No | No | No |
| Delete Amenity | Yes (Global) | No | No | No |

> **Note**: Amenities are global system resources managed exclusively by SUPER_ADMIN. All users can view amenities, but only SUPER_ADMIN can create, update, or delete them.

---

### Booking Management

| Operation | SUPER_ADMIN | TENANT_ADMIN | MANAGER | GUEST |
|-----------|-------------|--------------|---------|-------|
| Create Booking | No | Yes (Tenant) | Yes (Tenant) | Yes (Tenant) |
| List All Bookings | No | Yes (Tenant) | Yes (Tenant) | No |
| List Own Bookings | No | Yes | Yes | Yes |
| View Booking Details | No | Yes (Tenant) | Yes (Tenant) | Yes (Own) |
| Update Booking | No | Yes (Tenant) | Yes (Tenant) | Yes (Own) |
| Cancel Booking | No | Yes (Tenant) | Yes (Tenant) | Yes (Own) |
| Confirm Booking | No | Yes (Tenant) | Yes (Tenant) | No |

> **Note**: SUPER_ADMIN does not have access to booking management. This is tenant-scoped functionality.

---

### Payment Management

| Operation | SUPER_ADMIN | TENANT_ADMIN | MANAGER | GUEST |
|-----------|-------------|--------------|---------|-------|
| Create Payment Order | No | Yes (Tenant) | Yes (Tenant) | Yes (Tenant) |
| Verify Payment | No | Yes (Tenant) | Yes (Tenant) | Yes (Tenant) |
| List All Payments | No | Yes (Tenant) | Yes (Tenant) | No |
| List Own Payments | No | Yes | Yes | Yes |
| View Payment Details | No | Yes (Tenant) | Yes (Tenant) | Yes (Own) |
| Process Refund | No | Yes (Tenant) | Yes (Tenant) | No |

> **Note**: SUPER_ADMIN does not have access to payment management. This is tenant-scoped functionality.

---

### Review Management

| Operation | SUPER_ADMIN | TENANT_ADMIN | MANAGER | GUEST |
|-----------|-------------|--------------|---------|-------|
| Create Review | No | No | No | Yes* |
| List Reviews | No | Yes (Tenant) | Yes (Tenant) | Yes (Tenant) |
| View Review Details | No | Yes (Tenant) | Yes (Tenant) | Yes (Tenant) |
| Update Review | No | No | No | Yes (Own) |
| Delete Review | No | No | No | Yes (Own) |
| View Property Reviews | No | Yes (Tenant) | Yes (Tenant) | Yes (Tenant) |

**\*Note**: Reviews can only be created by GUEST users for properties with completed bookings. SUPER_ADMIN, TENANT_ADMIN, and MANAGER cannot create reviews.

---

### Message Management

| Operation | SUPER_ADMIN | TENANT_ADMIN | MANAGER | GUEST |
|-----------|-------------|--------------|---------|-------|
| Send Message | No | Yes (Tenant) | Yes (Tenant) | Yes (Tenant) |
| List All Messages | No | Yes (Tenant) | No | No |
| List Own Messages | No | Yes | Yes | Yes |
| View Message Details | No | Yes (Tenant) | Yes (Own) | Yes (Own) |
| View Conversation | No | Yes (Tenant) | Yes (Own) | Yes (Own) |

> **Note**: SUPER_ADMIN does not have access to messaging. This is tenant-scoped functionality.

---

### Dashboard & Analytics

| Operation | SUPER_ADMIN | TENANT_ADMIN | MANAGER | GUEST |
|-----------|-------------|--------------|---------|-------|
| View Tenant Dashboard | Yes (Tenant) | Yes (Tenant) | No | No |
| View Platform Dashboard | Yes (Global) | No | No | No |
| Filter by Date Range | Yes | Yes | No | No |

**Tenant Dashboard Metrics**: Total properties, bookings, revenue, occupancy rate  
**Platform Dashboard Metrics**: Total tenants, users, properties, bookings, system-wide revenue

---

### WebSocket & Real-time Communication

| Operation | SUPER_ADMIN | TENANT_ADMIN | MANAGER | GUEST |
|-----------|-------------|--------------|---------|-------|
| Connect to WebSocket | Yes | Yes | Yes | Yes |
| Send Real-time Messages | Yes (Tenant) | Yes (Tenant) | Yes (Tenant) | Yes (Tenant) |
| Receive Real-time Messages | Yes (Own) | Yes (Own) | Yes (Own) | Yes (Own) |

---

### Key Permission Principles

1. **Tenant Isolation**: All operational data (properties, bookings, payments, reviews, messages) is strictly tenant-scoped
2. **SUPER_ADMIN Limited Scope**: SUPER_ADMIN has global access ONLY to:
   - **Tenants**: Full CRUD operations across all tenants
   - **Users**: View, create, update, delete users across all tenants
   - **Amenities**: Global amenity catalog management
   - **Platform Dashboard**: System-wide analytics and metrics
3. **SUPER_ADMIN Restrictions**: SUPER_ADMIN does NOT have access to:
   - Properties, Bookings, Payments, Reviews, or Messages (all tenant-scoped)
   - These require tenant membership and appropriate role (TENANT_ADMIN, MANAGER, or GUEST)
4. **TENANT_ADMIN Privileges**: Full control within their tenant, including user management and all operational features
5. **MANAGER Privileges**: Can manage properties, amenities, bookings, and payments within their tenant
6. **GUEST Privileges**: Can create bookings, make payments, and write reviews for completed bookings
7. **Self-Service**: All roles can manage their own profile and view their own bookings/payments
8. **Review Restrictions**: Reviews can only be created by GUEST users for properties with completed bookings
9. **Message Privacy**: Users can only view conversations they are part of (except TENANT_ADMIN who can view all tenant messages)

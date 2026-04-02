# Finance Data Processing and Access Control Backend

## Project Overview

A Django-based RESTful backend API for a finance dashboard system that manages financial records with robust role-based access control. The system supports multiple user roles (Viewer, Analyst, Admin) with different permission levels and provides comprehensive financial data aggregation and analytics.

## Key Features

### 1. User and Role Management
- Three-tier role system: Viewer, Analyst, Admin
- User status management (active/inactive)
- Role-based access control on all endpoints
- User authentication and authorization

### 2. Financial Records Management
- Create, read, update, soft-delete financial transactions
- Transaction types: Income and Expense
- Pre-defined categories (Salary, Investment, Food, Transportation, Utilities, Entertainment, Healthcare, Education, Other)
- Advanced filtering by date range, category, and transaction type
- Pagination support for large datasets

### 3. Dashboard Summary APIs
- Total income and expense summaries
- Net balance calculations
- Category-wise breakdown (both income and expenses)
- Monthly trend analysis
- Recent activity tracking
- Period-based summaries (daily, weekly, monthly, yearly)
- Admin dashboard with system-wide analytics

### 4. Access Control
- Role-based endpoint protection using decorators
- Permission levels enforced at the API level
- Granular permissions for CRUD operations
- Soft delete functionality for data preservation

### 5. Data Validation and Error Handling
- Comprehensive input validation for all fields
- Custom validators for decimal, date, and choice fields
- Meaningful error responses with error codes
- HTTP status codes used appropriately
- Standardized response format

---

## Architecture

### Project Structure
```
finance_backend/
├── finance_backend/          # Main project settings
│   ├── urls.py               # Main URL routing
│   ├── settings.py           # Project settings
│   ├── wsgi.py               # WSGI configuration
│   └── asgi.py               # ASGI configuration
│
├── users/                    # User management app
│   ├── models.py             # Role and User models
│   ├── views.py              # User API views
│   ├── decorators.py         # Access control decorators
│   ├── utils.py              # Utility functions
│   ├── urls.py               # User app URLs
│   └── admin.py              # Django admin config
│
├── records/                  # Financial records app
│   ├── models.py             # FinancialRecord model
│   ├── views.py              # Record API views
│   ├── urls.py               # Records app URLs
│   └── admin.py              # Django admin config
│
├── dashboard/                # Dashboard analytics app
│   ├── models.py             # DashboardCache model
│   ├── views.py              # Dashboard API views
│   ├── urls.py               # Dashboard app URLs
│   └── admin.py              # Django admin config
│
├── manage.py                 # Django management script
├── db.sqlite3               # SQLite database
├── venv/                    # Python virtual environment
└── README.md                # This file
```

### Data Models

#### Role Model
- name: Choice field (viewer, analyst, admin)
- description: Text description of the role
- created_at: Timestamp

#### User Model
- username: Unique identifier
- email: Unique email address
- first_name, last_name: Name fields
- role: Foreign key to Role
- status: active/inactive
- created_at, updated_at: Timestamps
- last_login: Last login timestamp

#### FinancialRecord Model
- user: Foreign key to User (cascade on delete)
- amount: Decimal field (max 12 digits, 2 decimal places)
- transaction_type: income or expense
- category: Pre-defined category choice
- date: Transaction date
- description: Optional notes
- is_deleted: Soft delete flag
- created_at, updated_at: Timestamps

#### DashboardCache Model
- user: One-to-one relationship to User
- total_income: Aggregated income
- total_expense: Aggregated expense
- net_balance: Income - Expense
- record_count: Total records count
- last_updated: Cache refresh timestamp

---

## API Endpoints

### User Management (/api/users/)
Authentication Required: Yes (all endpoints)

| Method | Endpoint | Role Required | Description |
|---|---|---|---|
| GET | /api/users/current/ | Any | Get current authenticated user |
| GET | /api/users/list/ | Admin | List all users with filtering |
| GET | /api/users/id/ | Admin | Get user details |
| POST | /api/users/create/ | Admin | Create new user |
| PUT/PATCH | /api/users/id/update/ | Admin | Update user |
| DELETE | /api/users/id/delete/ | Admin | Delete user |
| GET | /api/users/roles/ | Admin | List available roles |

### Financial Records (/api/records/)
Authentication Required: Yes (all endpoints)

| Method | Endpoint | Role Required | Description |
|---|---|---|---|
| GET | /api/records/list/ | Any | List records (with filtering) |
| GET | /api/records/id/ | Any | Get record details |
| POST | /api/records/create/ | Analyst/Admin | Create new record |
| PUT/PATCH | /api/records/id/update/ | Analyst/Admin | Update record |
| DELETE | /api/records/id/delete/ | Analyst/Admin | Delete record (soft) |
| GET | /api/records/categories/ | Any | Get available categories |
| GET | /api/records/types/ | Any | Get transaction types |

---

## Setup Instructions

### Prerequisites
- Python 3.9+
- pip (Python package manager)

### Installation
1. Navigate to the project directory:
   cd d:\7Django\ZorvynProject

2. Activate the virtual environment:
   venv\Scripts\activate.bat

3. Install Django:
   pip install django

4. Run migrations:
   python manage.py migrate

5. Initialize database with sample data:
   python manage.py init_db

6. Create a superuser (optional):
   python manage.py createsuperuser

---

## API Usage

### Authentication
The system uses user ID authentication via query parameters or headers.
- Query parameter: ?user_id=1
- HTTP header: X-User-ID: 1

### Response Format
All responses follow a standard JSON format:

Success Response:
```json
{
  "status": "success",
  "message": "Operation successful",
  "data": { }
}
```

Error Response:
```json
{
  "status": "error",
  "message": "Error description",
  "code": "ERROR_CODE",
  "errors": { }
}
```

---

## Role Permissions Matrix

| Feature | Viewer | Analyst | Admin |
|---|---|---|---|
| View own records | Yes | Yes | Yes |
| Create records | No | Yes | Yes |
| Edit own records | No | Yes | Yes |
| Delete own records | No | Yes | Yes |
| View all records | No | No | Yes |
| Edit others' records | No | No | Yes |
| Delete others' records | No | No | Yes |
| View personal summary | Yes | Yes | Yes |
| View all summaries | No | No | Yes |
| Manage users | No | No | Yes |

---

## Error Codes Reference

- AUTH_REQUIRED (401): Authentication is required
- USER_INACTIVE (403): User account is inactive
- INSUFFICIENT_PERMISSIONS (403): User lacks required role
- USER_NOT_FOUND (404): User does not exist
- RECORD_NOT_FOUND (404): Financial record does not exist
- VALIDATION_ERROR (400): Input validation failed
- SERVER_ERROR (500): Internal server error

---

## Key Design Decisions

1. Soft Delete: Financial records use an is_deleted flag to maintain data integrity for auditing.
2. Pagination: Default page size is 20 items, capped at 100 to ensure performance.
3. Dashboard Cache: A one-to-one relationship with the User to improve query performance for analytics.
4. Role-Based Access Control: Implemented via decorators to centralize permission logic.

---

## Future Enhancements
1. JWT Authentication for secure token-based auth.
2. Data Export to CSV/Excel.
3. Recurring Transactions support.
4. Multi-currency support.
5. Unit Tests for comprehensive coverage.

---

Created: April 2, 2026
Framework: Django 5.2.7
Language: Python 3.x
Database: SQLite

# Library Management API (BookBuddy)

A backend REST API for managing users, books, and library loans, built with **FastAPI**, **SQLAlchemy**, and **PostgreSQL**.

The project focuses on clean API design, asynchronous database access, JWT authentication, role-based authorization, inventory management, and automated overdue-loan processing.

> **Project status:** In active development. Core authentication, user management, book management, and loan workflows are implemented. Some business rules and production-hardening improvements are still being developed.

---

## Features

### Authentication

* User registration
* User login with OAuth2 password flow
* JWT access tokens
* Password hashing with Argon2
* Protected API endpoints
* Current-user dependency
* Admin authorization dependency

### User Management

* Create users
* Retrieve users
* Retrieve a user by ID
* Update user information
* Prevent duplicate email addresses
* Admin-only user creation

### Book Management

* Create and manage books
* Track available book quantity
* Prevent borrowing when no copies are available
* Automatically decrease inventory when a book is borrowed
* Automatically increase inventory when a book is returned

### Loan Management

* Borrow books
* Prevent a user from having multiple active loans for the same book
* View personal loans
* View personal overdue loans
* Admin access to all loans
* Admin access to a specific user's loans
* Admin access to individual loans
* Admin-only loan returns
* Admin-only due-date updates
* Track borrowed, overdue, and returned loan states
* Record borrowing and return timestamps

### Automated Overdue Processing

The application uses **APScheduler** to automatically process loans whose due dates have passed and mark them as overdue.

---

## Tech Stack

| Technology  | Purpose                       |
| ----------- | ----------------------------- |
| Python      | Programming language          |
| FastAPI     | Web framework                 |
| SQLAlchemy  | ORM and database access       |
| PostgreSQL  | Relational database           |
| Pydantic    | Request/response validation   |
| JWT         | Authentication                |
| Argon2      | Password hashing              |
| APScheduler | Scheduled background jobs     |
| Alembic     | Database migrations           |
| Swagger UI  | Interactive API documentation |

The application uses SQLAlchemy's **async API** for asynchronous database operations.

---

## Architecture

The project follows a layered FastAPI structure:

```text
app/
├── database/
│   ├── database.py
│   ├── base.py
│   └── deps.py
│
├── models/
│   ├── user.py
│   ├── book.py
│   └── loan.py
│
├── schemas/
│   ├── user.py
│   ├── book.py
│   └── loan.py
│
├── routers/
│   ├── auth.py
│   ├── users.py
│   ├── books.py
│   └── loans.py
│
├── security/
│   └── security.py
│
└── main.py
```

The exact structure may evolve as the project grows.

---

## Authentication

Authentication uses OAuth2 password flow with JWT access tokens.

The login endpoint accepts the OAuth2 username/password form and returns a bearer token:

```json
{
  "access_token": "your-jwt-token",
  "token_type": "bearer"
}
```

Protected endpoints use the JWT to identify the authenticated user.

The authentication flow is:

```text
Login
  ↓
Verify email/password
  ↓
Create JWT
  ↓
Client sends Bearer token
  ↓
get_current_user()
  ↓
Authenticated User
```

### Admin Authorization

Administrative endpoints use a separate dependency:

```text
get_current_user()
        ↓
check is_admin
        ↓
get_current_admin()
```

This keeps authentication and authorization separate.

Authentication answers:

> Who is the user?

Authorization answers:

> Is this user allowed to perform this operation?

---

## Roles

The application currently supports two roles:

### Regular User

A regular user can:

* Authenticate
* Borrow books
* View their own loans
* View their own overdue loans

A user cannot:

* Access another user's loans
* Return a loan through the API
* Change a loan's due date
* Perform administrative loan lookups
* Create users through the administrative user endpoint

### Administrator

An administrator can:

* View all loans
* View overdue loans
* Look up a specific user's loans
* View individual loans
* Return books
* Change loan due dates
* Create users through the admin user endpoint
* Perform other administrative operations

---

# Loan System

Loans connect three entities:

```text
User
  │
  │ user_id
  ▼
Loan
  │
  │ book_id
  ▼
Book
```

A loan contains information such as:

* User
* Book
* Status
* Due date
* Borrowed date
* Returned date
* Creation timestamp
* Update timestamp

### Loan Statuses

The application currently supports:

```text
borrowed
overdue
returned
```

The database enforces the valid status values with a check constraint.

---

## Borrowing a Book

When a user creates a loan, the application:

1. Authenticates the user.
2. Checks that the requested book exists.
3. Checks that a copy is available.
4. Checks whether the user already has an active loan for that book.
5. Decreases the book quantity.
6. Creates the loan.
7. Returns the created loan with its related user and book.

The user ID is taken from the authenticated JWT rather than from the request body.

This prevents a user from creating a loan on behalf of another user.

---

## Returning a Book

Returning a book is an administrative operation.

When an administrator returns a loan, the application:

1. Finds the loan.
2. Ensures the loan exists.
3. Ensures it has not already been returned.
4. Finds the associated book.
5. Changes the loan status to `returned`.
6. Records the return timestamp.
7. Increases the available book quantity.

Both normal and overdue loans can be returned.

---

## Overdue Loans

APScheduler is used to periodically check loan due dates.

When a loan passes its due date, the scheduler can change its status from:

```text
borrowed
```

to:

```text
overdue
```

An overdue loan remains active until an administrator records the return.

---

# API Endpoints

The API is organized into several route groups.

## Authentication

### `POST /auth/registration`

Register a new user.

### `POST /auth/login`

Authenticate a user and receive a JWT access token.

Swagger UI can be used to authenticate through the OAuth2 password flow.

---

# Users

### `GET /users/`

Retrieve users.

### `GET /users/{user_id}`

Retrieve a user by ID.

### `PATCH /users/{user_id}`

Update a user's information.

### `POST /users/`

Create a user.

This operation is restricted to administrators.

---

# Loans

### `POST /loans/`

Borrow a book as the currently authenticated user.

The user ID is determined from the authentication token.

### `GET /loans/`

Retrieve loans.

Behavior depends on the authenticated user's role:

```text
Regular user → their own loans
Admin        → all loans
```

### `GET /loans/overdue`

Retrieve overdue loans.

```text
Regular user → their own overdue loans
Admin        → all overdue loans
```

### `GET /loans/user/{user_id}`

Retrieve all loans belonging to a specific user.

This is an **admin-only** operation.

### `GET /loans/{loan_id}`

Retrieve an individual loan.

This is an **admin-only** operation.

### `PATCH /loans/{loan_id}/return`

Return a loan.

This is an **admin-only** operation.

### `PATCH /loans/{loan_id}`

Update a loan's due date.

This is an **admin-only** operation.

---

# Authorization Model

The application deliberately separates user and administrative operations.

```text
                         ┌──────────────────┐
                         │  JWT Access Token │
                         └────────┬─────────┘
                                  │
                                  ▼
                         get_current_user()
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
               Regular User                 Admin User
                    │                           │
                    ▼                           ▼
             User operations              Admin operations
```

For resource-specific operations, ownership is determined from the authenticated user rather than trusting a user ID supplied by the client.

For example, when borrowing a book:

```python
user_id=current_user.id
```

rather than accepting:

```python
user_id=loan.user_id
```

This prevents users from impersonating other users.

---

# Database

The application uses PostgreSQL with SQLAlchemy's asynchronous engine.

Models currently include:

```text
User
Book
Loan
```

Relationships connect users and books to their loans.

For example:

```text
User
 └── loans

Book
 └── loans

Loan
 ├── user
 └── book
```

SQLAlchemy's `selectinload()` is used where related user and book information is required by the API response.

---

# Database Migrations

Alembic is used to manage database schema migrations.

Create a migration after changing the models:

```bash
alembic revision --autogenerate -m "describe your change"
```

Apply migrations:

```bash
alembic upgrade head
```

---

# Environment Variables

The application uses environment variables for configuration and secrets.

Example:

```env
DATABASE_URL=postgresql+asyncpg://username:password@localhost/library

SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Do **not** commit real credentials or secret keys to Git.

A local `.env` file should be excluded from version control.

Example `.gitignore` entry:

```gitignore
.env
__pycache__/
.venv/
```

---

# Running Locally

## 1. Clone the repository

```bash
git clone <https://github.com/adiomi90/bookbuddy_v1>
cd <your-project-directory>
```

## 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Linux/macOS:

```bash
source .venv/bin/activate
```

On Windows:

```bash
.venv\Scripts\activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 4. Configure environment variables

Create a `.env` file and configure the required database and authentication settings.

## 5. Run database migrations

```bash
alembic upgrade head
```

## 6. Start the API

```bash
uvicorn app.main:app --reload
```

The API should now be available locally.

---

# Interactive API Documentation

FastAPI automatically provides Swagger UI.

Once the application is running, open:

```text
/docs
```

Swagger allows you to:

* Inspect available endpoints
* Send requests
* Authenticate using OAuth2
* Test protected endpoints
* Inspect request and response schemas

The OpenAPI schema is also available through FastAPI's standard OpenAPI endpoint.

---

# Example Authentication Flow

### 1. Register

```http
POST /auth/registration
```

### 2. Login

```http
POST /auth/login
```

The server returns:

```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

### 3. Authorize Swagger

Use the **Authorize** button in Swagger UI and provide the user's credentials.

Swagger then sends the JWT as:

```http
Authorization: Bearer <token>
```

### 4. Access protected endpoints

The application extracts the token and resolves the authenticated user through:

```python
get_current_user()
```

Administrative endpoints additionally use:

```python
get_current_admin()
```

---

# Design Principles

This project is being developed around several backend principles.

### Authentication vs Authorization

Authentication identifies the user.

Authorization determines what that user is allowed to do.

### Never Trust Client Ownership

The API derives ownership from the authenticated user whenever possible.

For example:

```python
current_user.id
```

is used instead of trusting a user ID supplied by the client.

### Database Filtering

When users are restricted to their own resources, filtering is performed in the database:

```python
LoanModel.user_id == current_user.id
```

rather than retrieving everything and filtering it in Python.

### Build Queries Before Executing Them

Queries are constructed first and executed once:

```python
query = select(LoanModel)

if condition:
    query = query.where(...)

result = await db.execute(query)
```

This keeps the code efficient and easier to extend.

### Dependency-Based Authorization

Administrative authorization is handled through FastAPI dependencies rather than duplicated inside every endpoint:

```python
current_admin: UserModel = Depends(get_current_admin)
```

---

# Current Development Roadmap

Planned improvements include:

* [ ] Finalize selectable loan durations such as 7, 15, or 30 days
* [ ] Calculate due dates server-side from the selected loan duration
* [ ] Improve transaction safety for simultaneous borrowing requests
* [ ] Add stronger database constraints where appropriate
* [ ] Add automated tests
* [ ] Add pagination for large collections
* [ ] Improve error handling and validation
* [ ] Add structured logging
* [ ] Add production configuration
* [ ] Add Docker support
* [ ] Add CI/CD
* [ ] Improve API documentation
* [ ] Add more comprehensive authorization policies

---

# Project Goals

The main goal of this project is to build a realistic backend rather than simply create CRUD endpoints.

The project is used to explore practical backend concepts including:

* REST API design
* Authentication
* JWT
* OAuth2
* Role-based authorization
* Dependency injection
* Async SQLAlchemy
* Relational database design
* Database transactions
* Inventory management
* Background scheduling
* Data validation
* API security
* Clean project structure

---

## License

This project is currently for educational and development purposes.

Add a license here when the project is ready to be published under one.

---

## Author

Built as a backend development project focused on learning and applying real-world FastAPI architecture, authentication, authorization, database design, and API development.

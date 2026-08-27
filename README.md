# BookBuddy - Library Management API

A production-ready REST API for managing users, books, and library loans, built with **FastAPI**, **SQLAlchemy**, and **PostgreSQL**.

![Python](https://img.shields.io/badge/Python-3.13-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)
![Tests](https://img.shields.io/badge/Tests-14%2B-brightgreen)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)

## 🎯 Overview

BookBuddy demonstrates enterprise-level backend development practices including:
- ✅ **14+ automated tests** with 100% pass rate
- ✅ **Concurrency-safe operations** using `SELECT ... FOR UPDATE`
- ✅ **Full Docker containerization** with healthchecks
- ✅ **JWT authentication** with role-based access control
- ✅ **Background job processing** with APScheduler

---

## 🚀 Features

### Authentication & Authorization
- OAuth2 password flow with JWT tokens
- Argon2 password hashing (industry standard)
- Role-based access control (User vs Admin)
- Protected endpoints with dependency injection

### User Management
- User registration and authentication
- Duplicate email prevention
- Admin-only user creation
- User profile updates

### Book Inventory
- Create and manage book catalog
- Real-time quantity tracking
- Automatic stock updates on borrow/return
- Search and filter capabilities

### Loan System
- Borrow books with configurable due dates (7/15/30 days)
- **Prevent duplicate active loans** (same user, same book)
- **Enforce 5-loan limit** per user
- **Concurrency-safe borrowing** (prevents race conditions)
- Automatic overdue detection via APScheduler
- Admin-only loan returns and due date updates

### Background Jobs
- Daily overdue loan detection
- Automatic status updates for expired loans
- Non-blocking async execution

---

## 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| **Framework** | FastAPI |
| **Database** | PostgreSQL 15 |
| **ORM** | SQLAlchemy (async) |
| **Migrations** | Alembic |
| **Authentication** | JWT + Argon2 |
| **Validation** | Pydantic v2 |
| **Testing** | pytest + pytest-asyncio |
| **Background Jobs** | APScheduler |
| **Containerization** | Docker + Docker Compose |
| **API Docs** | Swagger UI (auto-generated) |

---

## 📁 Project Structure

```text
app/
├── database/
│   ├── database.py       # Database connection & session management
│   ├── base.py           # SQLAlchemy Base class
│   └── deps.py           # Dependency injection
├── models/
│   ├── user.py           # User model
│   ├── book.py           # Book model
│   └── loan.py           # Loan model with relationships
├── schemas/
│   ├── user.py           # Pydantic schemas for validation
│   ├── book.py
│   └── loan.py
├── routers/
│   ├── auth.py           # Authentication endpoints
│   ├── users.py          # User management
│   ├── books.py          # Book CRUD
│   └── loans.py          # Loan operations
├── security/
│   └── security.py       # JWT & password hashing
├── scheduled_task/
│   └── check_overdue.py  # Background job for overdue loans
└── main.py               # FastAPI app initialization
```

---

## 🏃 Quick Start

### Option 1: Docker (Recommended)

**Prerequisites:** Docker Desktop installed

```bash
git clone https://github.com/adiomi90/bookbuddy_v1
cd bookbuddy_v1
cp .env.example .env-docker
docker-compose up -d --build
docker-compose ps
docker-compose exec app pytest -v
```

Access the API at: `http://localhost:8000`
Interactive docs: `http://localhost:8000/docs`

### Option 2: Local Development

**Prerequisites:** Python 3.13+, PostgreSQL 15+

```bash
git clone https://github.com/adiomi90/bookbuddy_v1
cd bookbuddy_v1
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

---

## 🧪 Testing

The project includes a comprehensive test suite with **14+ tests** covering:

### Test Coverage
- ✅ Authentication (registration, login, token validation)
- ✅ User management (CRUD operations)
- ✅ Book inventory (stock tracking)
- ✅ Loan business logic (limits, duplicates, returns)
- ✅ **Concurrency safety** (race condition prevention)

### Running Tests

```bash
pytest -v
pytest tests/test_loans.py -v
pytest --cov=app tests/
```

### Concurrency Test Example

The `test_concurrent_loan_creation` test simulates 10 simultaneous requests to borrow the last copy of a book. It verifies that:
- Only 1 loan is created
- Inventory never goes negative
- Database locks prevent race conditions

---

## 📡 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Get JWT token

### Users
- `GET /users/me` - Get current user profile
- `PATCH /users/me` - Update profile
- `GET /users` - List all users (admin only)

### Books
- `GET /books` - List books (with search/filter)
- `GET /books/{id}` - Get book details
- `POST /books` - Create book (admin only)
- `PATCH /books/{id}` - Update book (admin only)
- `DELETE /books/{id}` - Delete book (admin only)

### Loans
- `POST /loans` - Borrow a book
- `GET /loans` - Get user's loans
- `GET /loans/overdue` - Get overdue loans (admin only)
- `PATCH /loans/{id}/return` - Return a book (admin only)
- `PATCH /loans/{id}` - Update due date (admin only)

---

## 🔐 Security Features

1. **Password Hashing**: Argon2 (winner of Password Hashing Competition)
2. **JWT Tokens**: Stateless authentication with configurable expiration
3. **CORS Protection**: Configurable cross-origin resource sharing
4. **Input Validation**: Pydantic schemas prevent injection attacks
5. **Role-Based Access**: Strict separation of user/admin permissions
6. **Database Transactions**: ACID-compliant operations with proper locking

---

## 🎓 Design Principles

### 1. Never Trust Client Data
All ownership is derived from JWT tokens, not client-provided IDs.

### 2. Database-Level Concurrency Control
Using `SELECT ... FOR UPDATE` to prevent race conditions.

### 3. Dependency Injection
FastAPI's dependency system for clean, testable code.

### 4. Async-First Architecture
Non-blocking I/O for high performance.

---

## 🐳 Docker Architecture

The Docker setup includes:
- **Multi-stage build** for optimized image size
- **Healthchecks** to ensure database readiness
- **Volume persistence** for database data
- **Environment isolation** via `.env-docker`

---

## 📊 Performance Considerations

- **Async Database Operations**: Non-blocking queries
- **Connection Pooling**: Efficient database connection reuse
- **Eager Loading**: `selectinload()` prevents N+1 query problems
- **Indexed Queries**: Optimized database lookups
- **Background Processing**: APScheduler for non-critical tasks

---

## 🔧 Troubleshooting

### Database Connection Issues

```bash
docker-compose ps
docker-compose logs db
docker-compose restart
```

### Test Failures

```bash
docker-compose exec app printenv TEST_DATABASE_URL
docker-compose exec app pytest -v -s
```

---

## 📝 Environment Variables

Create a `.env` or `.env-docker` file with:

```.env
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=bookbuddy_3
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/bookbuddy_3
TEST_DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/bookbuddy_3_test
SECRET_KEY=your-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```


```.env-docker
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=bookbuddy_3
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/bookbuddy_3
TEST_DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/bookbuddy_3_test
SECRET_KEY=your-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```
---

## 🚧 Roadmap

### Completed ✅
- [x] User authentication & authorization
- [x] JWT token management
- [x] Role-based access control
- [x] Book inventory management
- [x] Loan system with business rules
- [x] Concurrency-safe operations
- [x] Background job processing
- [x] Comprehensive test suite (14+ tests)
- [x] Docker containerization
- [x] Database migrations with Alembic

### Future Enhancements 🚀
- [ ] Rate limiting
- [ ] API versioning
- [ ] Email notifications for overdue books
- [ ] Advanced search with full-text search
- [ ] Redis caching layer
- [ ] CI/CD pipeline with GitHub Actions
- [ ] Cloud deployment (AWS/GCP)
- [ ] Monitoring & logging (Prometheus/Grafana)

---

## 📚 Learning Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Docker Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

## 📄 License

MIT License - feel free to use this as a learning resource.

---

## 👨‍💻 Author

Built with ❤️ as a comprehensive demonstration of modern backend development practices.

**Key Achievements:**
- 14+ automated tests with 100% pass rate
- Production-ready Docker setup
- Concurrency-safe database operations
- Clean, maintainable architecture

---

**Status:** ✅ Production-ready with comprehensive testing and Docker support

**Last Updated:** August 2026
# Production-Grade URL Shortener Backend

A high-performance, startup-grade URL shortener backend service built using **FastAPI**, **PostgreSQL** (via async SQLAlchemy), and **Redis**. Designed with clean architecture, rate limiting, SSRF protection, JWT-based authentication, caching, and database migrations.

---

## Technical Features & Architectural Design

- **Collision-Free Base62 Short Codes**: Instead of generating random short codes (which require db-retry loops on collision), we fetch the next sequence value from PostgreSQL (`urls_id_seq`) and convert it to Base62 (characters `0-9`, `a-z`, `A-Z`). This is extremely fast, collision-free, and guarantees short codes starting at 1-2 characters.
- **Two-Tier Redis Caching**:
  - **Cache Warming**: Newly shortened URLs are written to Redis immediately.
  - **Read Caching**: The redirection lookup route reads from Redis first. If there's a cache miss, it queries PostgreSQL and writes back to Redis with a 24-hour TTL.
  - **Cache Invalidation**: On URL deletion or expiry detection, keys are instantly evicted from Redis.
- **SSRF Prevention**: Before shortening a URL, the host is resolved to an IP address asynchronously. Loopback, private ranges (`10.x.x.x`, `192.168.x.x`, etc.), link-local, multicast, and reserved addresses are blocked to protect internal network services.
- **Non-Blocking Background Clicks**: Visitor clicks (IP, User-Agent, and Referrer) are logged asynchronously using FastAPI `BackgroundTasks` with short-lived database sessions. This ensures redirects are immediate (~ms) and database writes do not block the HTTP thread.
- **Custom Sliding-Window Rate Limiting**: Implement custom sliding window limiters using Redis pipelines to protect the shorten and redirection endpoints from abuse (e.g. 20 shorten/min, 120 redirects/min). Real client IPs are detected behind reverse proxies via `X-Forwarded-For` header inspection.
- **JWT Authentication**: Secure signup and login flow. Passwords are hashed using `bcrypt` and are never logged or exposed in HTTP responses.

---

## Directory Structure

```text
/
├── app/
│   ├── api/
│   │   ├── deps.py            # FastAPI dependency injection (get_db, get_redis, auth)
│   │   └── v1/
│   │       ├── auth.py        # SignUp & Login endpoints
│   │       ├── urls.py        # URL creation, deletion, listing
│   │       └── analytics.py   # Analytics dashboards for owners
│   ├── core/
│   │   ├── config.py          # Settings validation (Pydantic Settings)
│   │   ├── database.py        # SQLAlchemy Async engine and session factory
│   │   ├── exceptions.py      # Structured application domain exceptions
│   │   ├── limiter.py         # Redis sliding-window rate limiting dependency
│   │   ├── redis.py           # Async Redis client connection
│   │   └── security.py        # Bcrypt hashing & JWT utilities
│   ├── models/                # SQLAlchemy database models
│   ├── schemas/               # Pydantic validation schemas
│   ├── services/              # Pure business logic layer
│   └── main.py                # App entrypoint, CORS configuration, & root redirect
├── migrations/                # Alembic database schema migrations
├── tests/                     # Test suite
├── alembic.ini                # Alembic configuration
├── requirements.txt           # Python package dependencies
└── README.md                  # Project documentation
```

---

## System Requirements

- **Python**: 3.10 or newer
- **PostgreSQL**: 13 or newer (with an empty database named `url_shortener` created)
- **Redis**: 6 or newer

---

## Local Setup & Run Guide (Windows)

### 1. Clone & Setup Virtual Environment
Open PowerShell inside the project directory:
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Setup Local Services
- **PostgreSQL**: Install PostgreSQL using the official Windows installer. Create a database named `url_shortener`.
- **Redis**: You can run Redis on Windows using WSL (`wsl sudo service redis-server start`) or by downloading Memurai/Redis-Windows binaries. Ensure Redis is running on default port `6379`.

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and fill out your local service URLs:
```properties
DATABASE_URL="postgresql+asyncpg://<username>:<password>@localhost:5432/url_shortener"
REDIS_URL="redis://localhost:6379/0"
JWT_SECRET="generate-a-secure-random-key-in-production"
```

### 5. Run Database Migrations
Create the tables in your PostgreSQL database using Alembic:
```powershell
alembic upgrade head
```

### 6. Start the Server
```powershell
uvicorn app.main:app --reload
```
The server will start at `http://127.0.0.1:8000`. 
Interactive API documentation will be available at `http://127.0.0.1:8000/docs`.

---

## Running Tests
Run the automated test suite with pytest:
```powershell
pytest
```

---

## API Documentation

### Authentication
- `POST /api/v1/auth/signup`: Create a new user account.
- `POST /api/v1/auth/login`: Authenticate and receive a JWT token (OAuth2 form format).

### URL Management
- `POST /api/v1/urls/`: Shorten a URL. Accept target URL, custom alias (optional), and expiration datetime (optional). Returns short URL.
- `GET /api/v1/urls/`: List all URLs owned by the authenticated user.
- `DELETE /api/v1/urls/{short_code}`: Delete a shortened URL (removes it from DB and cache).

### Analytics
- `GET /api/v1/analytics/{short_code}`: Fetch total clicks and recent detailed logs (IP, User Agent, Referrer, timestamp) for URLs owned by you.

### Redirection
- `GET /{short_code}`: Resolve code and redirect to original URL via HTTP 307 (Temporary Redirect).

---

## Deployment Guide (Cloud Setup)

This application is ready to deploy directly to cloud providers like **Render** or **Railway** because it reads all secrets and configurations from standard environment variables.

### Deploying to Render
1. **Create Databases**:
   - Provision a **Render PostgreSQL** database and copy the connection string.
   - Provision a **Render Redis** instance and copy the connection string.
2. **Deploy the Web Service**:
   - Create a new **Web Service** on Render and link your GitHub repository.
   - Select **Python** as the environment.
   - Set **Build Command**: `pip install -r requirements.txt`
   - Set **Start Command**: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. **Environment Variables**:
   Add the following environment variables in the Render console:
   - `DATABASE_URL`: Set to your Render PostgreSQL connection string (replace `postgresql://` with `postgresql+asyncpg://` for async compatibility).
   - `REDIS_URL`: Set to your Render Redis connection string.
   - `JWT_SECRET`: A secure random password.
   - `ALLOWED_ORIGINS`: A comma-separated list of domains allowed to request your API (e.g. `https://yourdomain.com`).

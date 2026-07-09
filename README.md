# Production-Grade URL Shortener Backend (with Async Analytics Pipeline)

A high-performance URL shortener backend service built using **FastAPI**, **PostgreSQL** (via async SQLAlchemy), **Redis**, and **RabbitMQ** (via Celery). Designed with clean architecture, rate limiting, SSRF protection, JWT-based authentication, caching, database migrations, offline IP geolocation, and a periodic batch aggregation cron.

---

## Technical Features & Architectural Design

- **Collision-Free Base62 Short Codes**: Auto-incremented sequence keys are pulled from Postgres (`urls_id_seq`) and converted to Base62. Collision-free by design, fast, and generates extremely short urls.
- **Two-Tier Redis Caching**:
  - **Cache Warming**: Written to Redis immediately on URL creation.
  - **Read Caching**: Redirections resolve from Redis in `O(1)` time. Cache misses query PostgreSQL and warm Redis with a 24-hour TTL.
  - **Eviction**: Cache is updated/invalidated on URL modification or delete.
- **SSRF Prevention**: Hostnames are resolved to IP addresses asynchronously before shortening. Loopback (`127.0.0.0/8`), private ranges (`10.0.0.0/8`, `192.168.0.0/16`, etc.), link-local, multicast, and reserved addresses are blocked to protect internal network services.
- **Decoupled Asynchronous Analytics (Celery + RabbitMQ)**:
  - Redirections (`GET /{short_code}`) take single-digit milliseconds. They resolve the long URL from cache, enqueue a message to RabbitMQ via Celery, and redirect the user instantly.
  - A Celery Worker consumes the queue, parses user agents for OS/Browser/Device categories, resolves the client IP to a country code using a local MaxMind database, and writes the enriched data to `click_events` in Postgres.
- **Incremental Summary Table Aggregation (Celery Beat)**:
  - To prevent analytics requests from executing heavy scans on raw `click_events`, we use a scheduled Celery Beat task that aggregates clicks incrementally.
  - An `aggregated` boolean index column tracks raw clicks. The Beat task aggregates unaggregated rows, uses PostgreSQL `ON CONFLICT DO UPDATE` (upserts) to increment counters in summary tables (`clicks_daily_summary`, `clicks_country_summary`, `clicks_referrer_summary`, `clicks_device_summary`), and marks the batch as aggregated in one transaction.
  - The analytics dashboard retrieves data directly from summary tables in constant time.
- **JWT Authentication**: Signup and login route. Passwords hashed using `bcrypt`.
- **System Monitoring**: A `/health` check endpoint verifying connection status for PostgreSQL, Redis, and RabbitMQ.

---

## Directory Structure

```text
/
├── app/
│   ├── api/
│   │   ├── deps.py            # FastAPI dependency injection (get_db, auth)
│   │   └── v1/
│   │       ├── auth.py        # SignUp & Login endpoints
│   │       ├── urls.py        # URL creation, deletion, listing
│   │       ├── analytics.py   # Aggregated analytics dashboard
│   │       └── health.py      # Health checks for DB, Redis, RabbitMQ
│   ├── core/
│   │   ├── celery_app.py      # Celery instance, Beat cron schedule configuration
│   │   ├── config.py          # Settings validation (Pydantic Settings)
│   │   ├── database.py        # SQLAlchemy Async engine and session factory
│   │   ├── exceptions.py      # Structured application domain exceptions
│   │   ├── limiter.py         # Redis sliding-window rate limiting dependency
│   │   ├── redis.py           # Async Redis client connection
│   │   └── security.py        # Bcrypt hashing & JWT utilities
│   ├── models/                # SQLAlchemy database models
│   ├── schemas/               # Pydantic validation schemas
│   ├── services/              # Pure business logic layer
│   ├── tasks/
│   │   └── analytics.py       # Celery click logger & Beat aggregator tasks
│   └── main.py                # App entrypoint, CORS configuration, & root redirect
├── migrations/                # Alembic database schema migrations
├── tests/                     # Pytest suite
├── alembic.ini                # Alembic configuration
├── docker-compose.yml         # Container orchestration profile
├── Dockerfile                 # Docker container builder
├── download_geoip.py          # Script to download GeoIP MMDB files
├── locustfile.py              # Locust load testing script
├── requirements.txt           # Python package dependencies
└── README.md                  # Project documentation
```

---

## Quick Start via Docker Compose (Recommended)

To run the entire system (FastAPI, PostgreSQL, Redis, RabbitMQ, Celery Worker, Celery Beat) in containers:

### 1. Download GeoIP Database
Download the free Country geolocation database:
```powershell
python download_geoip.py
```

### 2. Boot Service Network
```powershell
docker-compose up --build
```
This command builds the application containers, runs all database migrations automatically, and starts the services:
- **FastAPI Backend**: `http://localhost:8000` (API Docs: `http://localhost:8000/docs`)
- **RabbitMQ Console**: `http://localhost:15672` (User: `guest`, Password: `guest`)

---

## Local Setup & Run Guide (Windows Hosts)

If running the services directly on your host machine without Docker:

### 1. Setup Virtual Environment
```powershell
# Create & Activate Virtual Environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install Dependencies
pip install -r requirements.txt
```

### 2. Download Geolocation Database
```powershell
python download_geoip.py
```

### 3. Setup services
- **PostgreSQL**: Install PostgreSQL. Create an empty database named `url_shortener`.
- **Redis**: Install Redis (via WSL or Memurai) and run it on port `6379`.
- **RabbitMQ**: Install RabbitMQ for Windows. Ensure it is running on default port `5672`.

### 4. Configure Environment
Copy `.env.example` to `.env` and fill out your database, redis, and rabbitmq configurations:
```properties
DATABASE_URL="postgresql+asyncpg://<username>:<password>@localhost:5432/url_shortener"
REDIS_URL="redis://localhost:6379/0"
CELERY_BROKER_URL="amqp://guest:guest@localhost:5672//"
CELERY_RESULT_BACKEND="redis://redis:6379/0"
JWT_SECRET="secure-random-key"
```

### 5. Run Migrations & Start Servers
```powershell
# Apply database migrations
alembic upgrade head

# Start FastAPI API
uvicorn app.main:app --reload

# Start Celery Worker (In a separate terminal)
celery -A app.core.celery_app.celery_app worker --loglevel=info -P solo

# Start Celery Beat Scheduler (In a separate terminal)
celery -A app.core.celery_app.celery_app beat --loglevel=info
```

---

## Running Tests
Ensure Python tests run cleanly:
```powershell
pytest
```

---

## Load Testing with Locust

We have included a Locust file to benchmark redirection performance.

### 1. Start Locust
Activate the virtual environment and launch Locust:
```powershell
locust
```

### 2. Open Load Test UI
Navigate to `http://localhost:8089` in your browser.
- **Number of users**: e.g., `100`
- **Spawn rate**: e.g., `10`
- **Host**: `http://localhost:8000` (or your FastAPI server URL)

### 3. Benchmarking Scenarios
You can use this load test script to compare response throughput and latencies:
1. **Cache Miss vs Cache Hit**: Test redirection when Redis cache is cleared compared to when Redis cache is warmed.
2. **Synchronous vs Asynchronous Logging**: Compare redirection speed when database writes are done synchronously (direct write) versus when click records are deferred asynchronously to RabbitMQ (Celery pipeline).

# Intelligent Media Processing Pipeline

A full-stack vehicle image processing system that accepts uploads, processes them asynchronously via Celery/Redis, runs heuristic image analysis (blur, brightness, duplicates, OCR, vehicle number validation, screenshot/tampering detection), and displays results in a React dashboard.

## Quick Start

```bash
cp .env.example .env
docker compose up --build
```

**Note:** For Docker, leave `VITE_API_BASE_URL` empty in `.env` so the frontend uses the nginx `/api` proxy. If your `.env` sets `VITE_API_BASE_URL=http://localhost:8000`, rebuild the frontend after clearing it.

| Service  | URL                          |
|----------|------------------------------|
| Frontend | http://localhost:3000        |
| Backend  | http://localhost:8000        |
| API Docs | http://localhost:8000/docs   |

## Architecture

```
Frontend (React) ──► FastAPI Backend ──► PostgreSQL
                         │                    ▲
                         ▼                    │
                    Redis Queue ──► Celery Worker
                         │
                    Local file storage (uploads volume)
```

### Processing Flow

1. User uploads image via frontend or `POST /api/v1/images/upload`
2. API validates file, saves to disk, creates DB record (`pending`), commits, enqueues Celery task
3. Worker picks up job, sets status `processing`, runs analyzers
4. Results saved to `analysis_results`, status set to `completed` (or `failed` with reason)
5. Frontend polls status until terminal state, then fetches results

### Queue Strategy

- **Broker**: Redis
- **Worker**: Celery with manual retry (max 3), exponential backoff; status stays `processing` during retries
- Jobs are committed to DB before enqueue to avoid race conditions
- Failed jobs store `failure_reason` and never remain stuck in `processing`

## Database Design

### `images`
Stores upload metadata: UUID `processing_id`, filenames, paths, dimensions, SHA-256, perceptual hash, status timestamps, failure reason.

### `analysis_results`
One-to-one with images. Stores per-analyzer scores/statuses and aggregated overall result.

Indexes on `processing_id`, `sha256_hash`, `perceptual_hash`, `status`, `upload_time`.

Migrations via Alembic (`alembic upgrade head` runs on backend startup).

## Image Analysis Methods

| Analyzer | Method | Notes |
|----------|--------|-------|
| Blur | Variance of Laplacian (OpenCV) | Heuristic thresholds |
| Brightness | Mean grayscale intensity | too_dark / acceptable / too_bright |
| Duplicate | SHA-256 exact + perceptual hash (imagehash) | Links to original processing ID |
| OCR | pytesseract | Non-fatal on failure |
| Vehicle Number | Regex + Indian state codes | Format validation only |
| Dimensions | Min size, aspect ratio | Corruption check |
| Screenshot | Aspect ratio, borders, moiré, EXIF | Probability score |
| Tampering | EXIF software, recompression, region variance | Not forensic |

Overall score/status aggregates weighted analyzer quality with detected issues list.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check (DB + Redis) |
| POST | `/api/v1/images/upload` | Upload image (returns processing_id) |
| GET | `/api/v1/images` | Paginated list with filters |
| GET | `/api/v1/images/stats/dashboard` | Dashboard statistics |
| GET | `/api/v1/images/{id}` | Full image + analysis details |
| GET | `/api/v1/images/{id}/status` | Processing status |
| GET | `/api/v1/images/{id}/results` | Analysis results |
| GET | `/api/v1/images/{id}/failure` | Failure reason |
| GET | `/api/v1/images/{id}/file` | Image file |

### Sample Upload Response

```json
{
  "processing_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "pending",
  "message": "Image accepted for processing"
}
```

### Sample Status Response

```json
{
  "processing_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "completed",
  "message": "Processing completed successfully",
  "processing_start_time": "2026-08-13T10:00:01Z",
  "processing_completion_time": "2026-08-13T10:00:03Z"
}
```

## Environment Variables

See `.env.example` for full list:

- `DATABASE_URL` / `DATABASE_URL_SYNC` — PostgreSQL connections
- `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`
- `UPLOAD_DIR`, `MAX_UPLOAD_SIZE_MB`, `ALLOWED_EXTENSIONS`
- `VITE_API_BASE_URL` — leave empty for Docker/nginx proxy; set to `http://localhost:8000` for direct backend access

## Local Development

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# Start postgres + redis (docker compose up postgres redis -d)
alembic upgrade head
uvicorn app.main:app --reload
celery -A app.workers.celery_app worker --loglevel=info
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Testing

```bash
# Inside backend container (recommended)
docker compose exec backend pytest -v

# Or locally with dependencies installed
cd backend && pytest -v
```

```bash
cd frontend && npm run build
```

## Failure Handling

- Invalid uploads return 400/413 with clear error codes
- OCR failures are caught per-analyzer (pipeline continues)
- Worker retries recoverable errors up to 3 times (status stays `processing` during retries)
- On final failure: status `failed`, `failure_reason` stored
- Global exception handler avoids leaking stack traces

## Trade-offs

- **Heuristics over ML**: Faster to ship, explainable, but not production-accuracy
- **Local file storage**: Simple for take-home; S3 would scale better
- **Single worker concurrency**: Sufficient for demo; scale workers horizontally in production
- **Synchronous analyzers in worker**: Acceptable for moderate images; could parallelize per-analyzer

## Scalability

- Stateless API behind load balancer
- Multiple Celery workers consuming same Redis queue
- PostgreSQL connection pooling (SQLAlchemy)
- Move uploads to object storage (S3/GCS)
- Add rate limiting and auth for production

## Known Limitations

- OCR accuracy depends on image quality and Tesseract limitations
- Vehicle number validation is format-only (no RTO lookup)
- Screenshot/tampering detection are heuristic, not forensic
- No authentication/authorization
- Perceptual duplicate search scans completed images (O(n) — would use ANN index at scale)

## Future Improvements

- Authentication and per-user quotas
- S3 storage with signed URLs
- ML-based blur/quality models
- Dedicated number-plate detection ROI
- Prometheus metrics and structured tracing
- WebSocket status push instead of polling
- Rate limiting and virus scanning

## AI Usage Disclosure

**Where AI was used:**
- Cursor AI assistant was used to scaffold project structure, boilerplate, and accelerate implementation of analyzers, API routes, frontend components, Docker config, and this README.

**What AI helped with:**
- Generating initial FastAPI/Celery/React patterns
- Drafting heuristic analyzer implementations
- Writing test stubs and documentation sections

**Where AI output was wrong or needed correction:**
- Docker Compose environment variable typos required manual fixes
- Celery task retry logic needed adjustment to avoid re-raising after max retries
- Enum handling with PostgreSQL required explicit Alembic migration types
- Frontend TypeScript strict mode required fixing optional chaining on API responses

**How generated code was validated:**
- `docker compose config` and `docker compose build`
- `pytest` for backend unit/API tests
- `npm run build` for frontend
- Manual end-to-end upload flow through browser and API
- Health endpoint and status polling verification

## Project Structure

```
media-processing-pipeline/
├── docker-compose.yml
├── .env.example
├── README.md
├── backend/
│   ├── app/
│   │   ├── api/v1/images.py
│   │   ├── analyzers/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── utils/
│   │   ├── workers/
│   │   └── main.py
│   ├── alembic/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── api/
    │   ├── components/
    │   ├── pages/
    │   └── types/
    ├── Dockerfile
    └── package.json
```

## Technologies

**Backend:** Python 3.12, FastAPI, PostgreSQL, SQLAlchemy, Alembic, Pydantic, OpenCV, Pillow, NumPy, pytesseract, Redis, Celery, pytest

**Frontend:** React, TypeScript, Vite, Tailwind CSS, Axios, TanStack Query, React Router, Recharts

**Infrastructure:** Docker, Docker Compose, Nginx

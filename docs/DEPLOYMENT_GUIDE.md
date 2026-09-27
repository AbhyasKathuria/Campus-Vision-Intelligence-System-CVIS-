# CVIS — Production Deployment & Operations Guide

## 1. System Requirements

### Recommended Hardware (Standard University Department)
- **CPU**: 4 to 8 vCPUs (Intel Xeon / AMD EPYC)
- **RAM**: 8 GB to 16 GB
- **Storage**: 100 GB SSD (NVMe recommended for media storage)
- **GPU**: Optional. The ML inference pipeline is fully CPU-optimized using ONNX Runtime and OpenCV DNN.
- **OS**: Ubuntu 22.04 LTS, Debian 12, or Windows Server 2022

---

## 2. Docker Compose Production Deployment

The quickest way to deploy the entire CVIS monorepo is via Docker Compose:

### Step 1: Clone & Configure Environment
```bash
git clone https://github.com/your-org/cvis.git
cd cvis/infra
cp .env.example .env
```

Edit `.env` to configure secure secrets:
```ini
ENVIRONMENT=production
POSTGRES_PASSWORD=your_ultra_secure_db_password_here
JWT_SECRET=generate_a_random_64_character_hex_string_here
DEFAULT_RETENTION_DAYS=30
SIMILARITY_THRESHOLD=0.65
```

### Step 2: Build & Start Services
```bash
docker compose up -d --build
```

### Step 3: Verify Service Health
```bash
docker compose ps
```
All containers should report `healthy` or `running`:
- `cvis_postgres` (PostgreSQL 16)
- `cvis_redis` (Redis 7)
- `cvis_ml_service` (FastAPI ML Inference)
- `cvis_backend` (FastAPI Core)
- `cvis_celery_worker` (Background Ingestion & Purge Worker)
- `cvis_frontend` (Nginx + React SPA)

---

## 3. Production Nginx & SSL / TLS Configuration

For production deployment with HTTPS, point your domain (e.g. `cvis.university.edu`) to the server and terminate TLS at an edge Nginx / Caddy reverse proxy:

```nginx
server {
    listen 443 ssl http2;
    server_name cvis.university.edu;

    ssl_certificate /etc/letsencrypt/live/cvis.university.edu/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cvis.university.edu/privkey.pem;

    client_max_body_size 500M; # Support bulk zip uploads

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

---

## 4. Maintenance Operations

### Manual Retention Purge
To manually trigger the retention purge job:
```bash
curl -X POST http://localhost:8000/api/v1/system/purge-expired \
  -H "Authorization: Bearer <ADMIN_JWT_TOKEN>"
```

### Automated Database Backup
```bash
docker exec -t cvis_postgres pg_dumpall -c -U cvis_user > cvis_backup_$(date +%Y%m%d).sql
```

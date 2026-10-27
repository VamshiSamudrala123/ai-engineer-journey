# Build InsightForge's React dashboard using Node.js.
FROM node:22-bookworm-slim AS frontend
WORKDIR /build/dashboard
COPY dashboard/package.json dashboard/package-lock.json ./
RUN npm ci
COPY dashboard/ ./
RUN npm run build

# Run the FastAPI application with a stable Python runtime.
FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    INSIGHTFORGE_ENV=production
WORKDIR /app
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY . ./
COPY --from=frontend /build/dashboard/dist /app/dashboard/dist

# Never start a cloud container with local development credentials.
# Production access middleware must fail closed until the host supplies
# INSIGHTFORGE_ACCESS_USERNAME and INSIGHTFORGE_ACCESS_PASSWORD.
EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]

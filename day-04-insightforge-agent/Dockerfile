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

# Render provides PORT. Production credentials must be configured on the host.
# Generate the tiny fictional dataset only when explicitly opted in; the image
# still excludes any real or large banking datasets.
EXPOSE 8000
CMD ["sh", "-c", "if [ \"${INSIGHTFORGE_DEMO_DATA:-false}\" = \"true\" ]; then python generate_demo_data.py; fi; exec uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]

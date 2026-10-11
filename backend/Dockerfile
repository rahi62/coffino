FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN addgroup --system cafino && adduser --system --ingroup cafino cafino \
    && python manage.py collectstatic --noinput \
    && chmod 755 /app/start-web.sh \
    && chown -R cafino:cafino /app
USER cafino
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=8s --start-period=90s --retries=3 \
    CMD curl --fail --silent --show-error --max-time 5 "http://127.0.0.1:${PORT:-8000}/api/v1/health/" >/dev/null || exit 1
CMD ["/bin/sh", "/app/start-web.sh"]

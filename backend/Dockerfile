FROM python:3.12-slim
# Coolify HTTP healthchecks run inside the final application container.
# The slim Python base does not guarantee curl/wget are installed.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && command -v curl
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN addgroup --system cafino && adduser --system --ingroup cafino cafino \
    && python manage.py collectstatic --noinput \
    && chmod 755 /app/start-web.sh \
    && chown -R cafino:cafino /app
USER cafino
EXPOSE 8000
CMD ["/bin/sh", "/app/start-web.sh"]

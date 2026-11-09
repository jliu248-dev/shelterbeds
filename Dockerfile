FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    FLASK_APP=wsgi.py \
    PORT=8080

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as a non-root user.
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

# Apply database migrations, then start gunicorn on the port Cloud Run gives us.
CMD flask db upgrade && exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 wsgi:app

FROM python:3.12-slim

# Non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY app/ app/

# Create data directory
RUN mkdir -p data/documentos data/imagens data/videos && \
    chown -R appuser:appuser /app

USER appuser

# Cloud Run uses PORT env variable (default 8080)
ENV PORT=8080

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]

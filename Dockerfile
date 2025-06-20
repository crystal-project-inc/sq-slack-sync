FROM python:3.10-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create a non-root user and set permissions
RUN useradd -m appuser && \
    chown -R appuser:appuser /app

USER appuser

# Environment variables can be overridden at runtime
ENV SQUADCAST_TENANCY=squadcast.com
ENV LOG_LEVEL=INFO

# Command to run the application
CMD ["python", "main.py"]

#FROM python:3.12-slim
#WORKDIR /app
## Add required build dependencies
#RUN apt-get update && apt-get install -y gcc libpq-dev
#COPY requirements.txt requirements.txt
#RUN pip install --no-cache-dir -r requirements.txt
#COPY app.py .
#CMD ["python", "app.py"]

FROM python:3.12-slim

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user (optional, for security)
RUN adduser --disabled-password --gecos '' flaskuser

WORKDIR /app

# Install Python dependencies first (for better caching)
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy only the app code (not the whole context)
COPY app.py .
COPY static/theme.* ./static/

# Use non-root user (optional)
USER flaskuser

# Expose the port Flask runs on
EXPOSE 5000

# Use gunicorn for production, or fallback to Flask's dev server for testing
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
# For development, you can use:
# CMD ["python", "app.py"]
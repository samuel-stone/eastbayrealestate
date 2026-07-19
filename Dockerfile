# Use the official Microsoft Playwright Python image
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Install root SSL certificates so psycopg2 can verify Aiven
RUN apt-get update && apt-get install -y ca-certificates

# Set the working directory inside the container
WORKDIR /app
ENV PYTHONPATH=/app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN playwright install chromium
RUN playwright install-deps chromium

COPY . .

CMD ["python3", "automation_engine/worker.py"]

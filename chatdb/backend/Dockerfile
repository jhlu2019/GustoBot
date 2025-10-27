FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create necessary directories
RUN mkdir -p app/api/api_v1/endpoints
RUN mkdir -p app/core
RUN mkdir -p app/db
RUN mkdir -p app/models
RUN mkdir -p app/schemas
RUN mkdir -p app/services

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

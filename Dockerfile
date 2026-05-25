FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev gcc g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY datasets/ ./datasets/
COPY "QS World University Rankings 2025.csv" ./
COPY talash/ ./talash/

EXPOSE 8000

CMD ["uvicorn", "talash.main:app", "--host", "0.0.0.0", "--port", "8000"]

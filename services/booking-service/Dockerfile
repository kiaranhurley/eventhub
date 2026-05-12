FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh

COPY main.py .

CMD ["/wait-for-it.sh", "rabbitmq:5672", "--", "/wait-for-it.sh", "redis:6379", "--", "python", "main.py"]

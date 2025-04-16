FROM python:3.9-slim as builder

WORKDIR /app
COPY . .

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --user -r requirements.txt

FROM python:3.9-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY --from=builder /app .

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app

CMD ["python", "-m", "igidir"]
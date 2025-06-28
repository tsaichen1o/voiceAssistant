FROM python:3.12-slim-bookworm as builder

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN addgroup --system nonroot && adduser --system --group nonroot
WORKDIR /app
USER nonroot

COPY --from=builder --chown=nonroot:nonroot /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder --chown=nonroot:nonroot /usr/local/bin /usr/local/bin

COPY --chown=nonroot:nonroot . .

EXPOSE 8080

CMD ["gunicorn", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080", "--timeout", "120", "main:app"]
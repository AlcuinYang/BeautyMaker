FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md ./
RUN pip install --upgrade pip && pip install .

COPY gateway gateway
COPY services services

CMD ["uvicorn", "gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]

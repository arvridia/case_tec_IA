FROM python:3.11-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

# instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copiar código
COPY . .

# API exposta na porta 8000
EXPOSE 8000

# roda apenas a API (FastAPI)
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]

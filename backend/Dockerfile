FROM python:3.9-slim

WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy only necessary files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

COPY app ./app

# Set default PORT environment variable
ENV PORT=8080

EXPOSE 8080

# Use CMD to run Uvicorn without reload in all environments
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port $PORT"]

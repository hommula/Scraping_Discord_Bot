FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync 

COPY scrap_yahoo.py .

CMD ["uv", "run", "scrap_yahoo.py"]
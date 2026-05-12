# ── Base image ────────────────────────────────────────────────────────────────
FROM python:3.10-slim

# ── System deps (slim image needs these for some wheels) ──────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ─────────────────────────────────────────────────────────
WORKDIR /code

# ── Python dependencies ───────────────────────────────────────────────────────
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# ── Application code ──────────────────────────────────────────────────────────
COPY ./app       /code/app
COPY ./templates /code/templates

# ── Ensure downloads directory exists inside container ────────────────────────
RUN mkdir -p /code/downloads

# ── Python path so `from app.xxx import` works ────────────────────────────────
ENV PYTHONPATH=/code

# ── Hugging Face Spaces runs as a non-root user; set permissions ──────────────
RUN chmod -R 777 /code/downloads

# ── Port exposed (must match README.md app_port) ──────────────────────────────
EXPOSE 7860

# ── Start server ──────────────────────────────────────────────────────────────
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
ARG PYTHON_VERSION=3.12.10
FROM python:${PYTHON_VERSION}-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /code 

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY downloader.py ./ 

RUN useradd -m appuser
USER appuser

ENTRYPOINT ["python", "downloader.py"]
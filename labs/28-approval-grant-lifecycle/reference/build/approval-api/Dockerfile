ARG PYTHON_IMAGE=python:3.12-slim
FROM ${PYTHON_IMAGE}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
RUN if command -v apk >/dev/null 2>&1; then \
        apk upgrade --no-cache; \
    else \
        apt-get update \
        && apt-get upgrade -y \
        && rm -rf /var/lib/apt/lists/*; \
    fi
COPY requirements-runtime.txt /tmp/requirements-runtime.txt
RUN pip install --no-cache-dir -r /tmp/requirements-runtime.txt
COPY services/approval-api/approval_api /app/approval_api
COPY database/migrations/control-db /app/migrations

USER 65532:65532
EXPOSE 8001
CMD ["uvicorn", "approval_api.main:app", "--host", "0.0.0.0", "--port", "8001"]

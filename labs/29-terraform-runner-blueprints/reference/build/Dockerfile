ARG TERRAFORM_IMAGE=hashicorp/terraform:1.16.1
ARG PYTHON_IMAGE=python:3.12-slim

FROM ${TERRAFORM_IMAGE} AS terraform
FROM ${PYTHON_IMAGE}
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN if command -v apk >/dev/null 2>&1; then \
        apk upgrade --no-cache \
        && apk add --no-cache ca-certificates openssh-client; \
    else \
        apt-get update \
        && apt-get upgrade -y \
        && apt-get install -y --no-install-recommends ca-certificates openssh-client \
        && rm -rf /var/lib/apt/lists/*; \
    fi
COPY --from=terraform /bin/terraform /usr/local/bin/terraform
COPY services/terraform-runner/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY services/terraform-runner/terraform_runner /app/terraform_runner
COPY terraform/modules /workspace/terraform/modules
COPY terraform/catalog.json /workspace/terraform/catalog.json
COPY terraform/supply-chain-lock.json /workspace/terraform/supply-chain-lock.json
COPY ansible /workspace/ansible
RUN mkdir -p /work /state && chown -R 65532:65532 /work /state
USER 65532:65532
CMD ["python", "-m", "terraform_runner.main"]

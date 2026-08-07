# Python patch version and multi-arch image digest are both pinned. Update only
# together with ops/runtime/PYTHON_VERSION and the locked dependency set.
ARG PYTHON_IMAGE=python:3.14.4-slim-bookworm@sha256:fc74d22ffd0d5ac395a4b7bdda75a4539758862c49ebf3005647084631e63789
FROM ${PYTHON_IMAGE}

LABEL org.opencontainers.image.title="shuheng-quant" \
      org.opencontainers.image.description="枢衡 qbase/taosha deterministic runtime"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/opt/quant \
    TZ=Asia/Shanghai

RUN groupadd --gid 10001 shuheng \
    && useradd --uid 10001 --gid 10001 --create-home --shell /bin/bash shuheng \
    && install -d --owner=shuheng --group=shuheng /opt/quant

WORKDIR /opt/quant

COPY ops/runtime/requirements-qbase-ingest.lock /tmp/requirements.lock
ARG PYPI_INDEX_URL=https://pypi.org/simple
RUN python -m pip install --disable-pip-version-check --no-cache-dir \
      --index-url "${PYPI_INDEX_URL}" \
      --requirement /tmp/requirements.lock \
    && rm /tmp/requirements.lock

COPY --chown=shuheng:shuheng . /opt/quant

# Fail image construction before deployment if new code exceeds the size
# budget or any grandfathered hotspot grows beyond its reviewed baseline.
RUN python -m ops.verify_code_size

USER shuheng

# The image has no long-running service. Every research/ingest operation must be
# an explicit one-shot command, so the safe default is an environment audit.
CMD ["python", "-m", "ops.verify_runtime", "--strict"]

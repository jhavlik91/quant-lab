FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY examples ./examples
RUN pip install --no-cache-dir .

RUN useradd --create-home quantlab && mkdir -p /data && chown quantlab:quantlab /data
USER quantlab
VOLUME ["/data"]
ENV QUANT_LAB_DB=/data/quant_lab.db

ENTRYPOINT ["quant-lab"]
CMD ["job", "examples/job.json"]

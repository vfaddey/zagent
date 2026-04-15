FROM python:3.13-slim

WORKDIR /opt/zagent

COPY packages/runtime /opt/zagent/packages/runtime

RUN pip install --no-cache-dir /opt/zagent/packages/runtime

ENTRYPOINT ["zagent-runtime"]


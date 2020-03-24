# Template Dockerfile for Python 3-based RPC microservices.
# Pass in a Docker build arg module to build the relevant module.

FROM python:3

WORKDIR /usr/src/app

# Install requirements
COPY build/nameko/requirements.txt requirements.txt
RUN pip install -r requirements.txt

ARG module

# Copy source code
COPY src/${module} ./service

# Copy config
COPY build/nameko/config.yaml /etc/nameko/config.yaml

ENTRYPOINT [ "nameko", "run", "service", "--config=/etc/nameko/config.yaml" ]

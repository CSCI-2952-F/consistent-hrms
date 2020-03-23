# Template Dockerfile for Python 3-based RPC microservices.
# Pass in a Docker build arg module to build the relevant module.

FROM python:3

ARG module

WORKDIR /usr/src/app

# Install requirements
COPY build/nameko_service/requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copy source code
COPY src/${module} ./${module}

ENTRYPOINT [ "nameko" ]

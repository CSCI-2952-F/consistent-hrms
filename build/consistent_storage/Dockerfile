# Dockerfile for consistent_storage.

FROM python:3.7

WORKDIR /usr/src/app

# Install requirements
COPY build/consistent_storage/requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copy source code
COPY src .

# Copy config
COPY build/nameko/config.yaml /etc/nameko/config.yaml

# Expose HTTP server
EXPOSE 80

ENTRYPOINT [ "nameko", "run", "consistent_storage", "--config=/etc/nameko/config.yaml" ]

FROM python:3.7

WORKDIR /usr/src/app

# Install requirements
COPY src/bigchaindb_client/requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copy source code
COPY src .

# Expose HTTP server
EXPOSE 80

ENTRYPOINT [ "python", "-m", "bigchaindb_client.main", "bigchaindb_client/main.py" ]

FROM python:3

WORKDIR /usr/src/app

# Install requirements
COPY build/consistent_storage/requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Add source code
COPY src/consistent_storage ./consistent_storage

# Run the Nameko service
ENTRYPOINT [ "nameko" ]

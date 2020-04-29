FROM python:3.7

WORKDIR /usr/src/app

# Install requirements
COPY build/python/requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copy source code
COPY src .

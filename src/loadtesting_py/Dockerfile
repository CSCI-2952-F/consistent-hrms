FROM python:3.7

WORKDIR /usr/src/app

# Install dependencies
COPY src/loadtesting_py/requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Add application code
COPY src .
COPY data/patient_cards .

CMD [ "bash", "-c", "echo 'To run load test, use docker/docker-compose exec to invoke manually.' && tail -f /dev/null" ]

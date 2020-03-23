FROM python:3

WORKDIR /usr/src/app

# Install requirements
COPY build/frontend/requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Add source code
COPY src/frontend .

EXPOSE 80

CMD [ "python", "main.py" ]

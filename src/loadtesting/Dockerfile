FROM golang:1.14

WORKDIR /go/src/github.com/irvinlim/cs2952f-hrms/src/loadtesting

# Install dependencies
COPY go.mod go.sum ./
RUN go mod download

# Add application code and install binary
COPY . .
RUN go install -v ./...

CMD [ "bash", "-c", "echo 'To run load test, use docker/docker-compose exec to invoke manually.' && tail -f /dev/null" ]

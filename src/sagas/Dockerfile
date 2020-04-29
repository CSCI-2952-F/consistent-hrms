FROM golang:1.14

WORKDIR /go/src/github.com/irvinlim/cs2952f-hrms/src/sagas

# Install dependencies
COPY go.mod go.sum ./
RUN go mod download

# Add application code and install binary
COPY . .
RUN go install -v ./...

ENTRYPOINT [ "sagas" ]

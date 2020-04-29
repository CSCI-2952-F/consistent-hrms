FROM golang:1.14

WORKDIR /go/src/github.com/irvinlim/cs2952f-hrms/src/discovery

# Install dependencies
COPY go.mod go.sum ./
RUN go mod download

# Add application code and install binary
COPY . ./
RUN go install -v ./...

ENTRYPOINT [ "discovery_client" ]

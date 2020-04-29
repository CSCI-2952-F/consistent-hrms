FROM golang:1.14

WORKDIR /go/src/discovery

# Install dependencies
COPY go.mod go.sum ./
RUN go mod download

# Add application code and install binary
COPY . ./
RUN go install -v ./...

ENTRYPOINT [ "discovery_client" ]

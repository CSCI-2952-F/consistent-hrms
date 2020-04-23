FROM golang:1.14

# Built binary will be `discovery`
WORKDIR /go/src/discovery

# Install dependencies
COPY go.mod go.sum ./
RUN go mod download

# Add application code and install binary
COPY *.go ./
RUN go install -v

ENTRYPOINT [ "discovery" ]

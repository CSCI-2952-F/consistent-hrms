FROM golang:1.14

# Built binary will be `sagas`
WORKDIR /go/src/sagas

# Install dependencies
COPY go.mod go.sum ./
RUN go mod download

# Add application code and install binary
COPY *.go ./
RUN go install -v

ENTRYPOINT [ "sagas" ]

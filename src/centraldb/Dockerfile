FROM golang:1.14

# Built binary will be `centraldb`
WORKDIR /go/src/github.com/irvinlim/cs2952f-hrms/src/centraldb

# Install dependencies
COPY go.mod go.sum ./
RUN go mod download

# Add application code and install binary
COPY *.go ./
RUN go install -v

ENTRYPOINT [ "centraldb" ]

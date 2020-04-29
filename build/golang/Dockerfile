FROM golang:1.14

# Copy all golang libraries
WORKDIR /go/src/github.com/irvinlim/cs2952f-hrms/src
# COPY src/centraldb ./centraldb
COPY src/discovery ./discovery
COPY src/loadtesting ./loadtesting
# COPY src/sagas ./sagas

# Copy application code and install binary
RUN go install -v ./...

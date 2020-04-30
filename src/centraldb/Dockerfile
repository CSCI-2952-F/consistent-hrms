FROM golang:1.14 AS builder

ENV PKG github.com/irvinlim/cs2952f-hrms/src/centraldb
WORKDIR /go/src/${PKG}

# Install dependencies
COPY go.mod go.sum ./
RUN go mod download

# Add application code and build binary
COPY . ./
RUN CGO_ENABLED=0 GOOS=linux go build -installsuffix cgo -o /go/centraldb ./...

# Move the built binary into the tiny alpine linux image
FROM alpine:latest

RUN apk --no-cache add ca-certificates && rm -rf /var/cache/apk/*
WORKDIR /app
ENV PATH $PATH:/app

COPY --from=builder /go/centraldb .

ENTRYPOINT [ "centraldb" ]

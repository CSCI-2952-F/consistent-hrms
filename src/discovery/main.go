package main

import (
	"context"
	"log"
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"

	"google.golang.org/grpc"
)

var (
	serviceDiscovery ServiceDiscovery
	keyPrefix        string

	hospitalId     string
	hospitalName   string
	registeredTime time.Time
)

type ServiceDiscovery interface {
	Register(ctx context.Context, value RegisterValue) error
	Renew(ctx context.Context, duration time.Duration)
	Revoke(ctx context.Context) error
	ListValues(ctx context.Context) ([]RegisterValue, error)
}

type RegisterValue struct {
	Id             string `json:"id"`
	Name           string `json:"name"`
	RegisteredTime int64  `json:"registered_time"`
}

func main() {
	ctx, cancelFunc := context.WithCancel(context.Background())

	// Parse environment variables
	hospitalId = os.Getenv("HOSPITAL_ID")
	if hospitalId == "" {
		log.Fatalf("HOSPITAL_ID not set")
	}
	hospitalName = os.Getenv("HOSPITAL_NAME")
	if hospitalName == "" {
		log.Fatalf("HOSPITAL_NAME not set")
	}
	grpcListenAddr := os.Getenv("GRPC_LISTEN_ADDR")
	etcdAddr := os.Getenv("ETCD_ADDR")
	keyPrefix = os.Getenv("KEY_PREFIX")

	leaseExpiry := 2 * time.Minute
	expiryEnv := os.Getenv("LEASE_EXPIRY")
	if expiryEnv != "" {
		expiry, err := time.ParseDuration(expiryEnv)
		if err != nil {
			log.Fatalf("Could not parse expiry: %s", err)
		}
		leaseExpiry = expiry
	}

	// Create etcd service discovery
	etcd, err := NewEtcdServiceDiscovery(etcdAddr, keyPrefix, leaseExpiry)
	if err != nil {
		log.Fatal(err)
	}

	serviceDiscovery = etcd

	// Prepare register value
	registeredTime = time.Now()
	value := RegisterValue{
		Id:             hospitalId,
		Name:           hospitalName,
		RegisteredTime: registeredTime.Unix(),
	}

	// Register ourselves on etcd
	if err := serviceDiscovery.Register(ctx, value); err != nil {
		log.Fatal(err)
	}

	// Create gRPC server
	lis, err := net.Listen("tcp", grpcListenAddr)
	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}
	grpcServer := grpc.NewServer()
	RegisterHospitalDiscoveryServer(grpcServer, NewServer(etcd))

	// Register signal handlers
	done := make(chan bool)
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, os.Interrupt, syscall.SIGTERM)

	go func() {
		<-quit
		log.Println("Shutting down.")

		// Cancel root context
		cancelFunc()

		// Revoke lease
		if err := serviceDiscovery.Revoke(context.Background()); err != nil {
			log.Println(err)
		}

		close(done)
	}()

	// Continuously renew the lease in the background
	go serviceDiscovery.Renew(ctx, 5*time.Second)

	// Start gRPC server
	log.Printf("Starting gRPC server on %s.\n", grpcListenAddr)
	if err := grpcServer.Serve(lis); err != nil {
		log.Fatal(err)
	}

	<-done
	log.Println("Shutdown completed.")
}

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

	hospitalId         string
	hospitalName       string
	hospitalPublicKey  []byte
	hospitalPrivateKey []byte
	registeredTime     time.Time

	keyStorage *KeyStorage
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
	GatewayAddr    string `json:"gateway_addr"`
	PublicKey      []byte `json:"public_key"`
	RegisteredTime int64  `json:"registered_time"`
}

func main() {
	ctx, cancelFunc := context.WithCancel(context.Background())

	// Service metadata environment variables
	hospitalId = os.Getenv("HOSPITAL_ID")
	if hospitalId == "" {
		log.Fatalf("HOSPITAL_ID not set")
	}
	hospitalName = os.Getenv("HOSPITAL_NAME")
	if hospitalName == "" {
		log.Fatalf("HOSPITAL_NAME not set")
	}
	hospitalGatewayAddr := os.Getenv("HOSPITAL_GATEWAY_ADDR")
	if hospitalGatewayAddr == "" {
		log.Fatalf("HOSPITAL_GATEWAY_ADDR not set")
	}

	// Configuration environment variables
	grpcListenAddr := os.Getenv("GRPC_LISTEN_ADDR")
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

	// Initialize key storage
	storage, err := NewKeyStorage(keyPath)
	if err != nil {
		log.Fatalf("could not initialize key storage: %s", err)
	}
	keyStorage = storage

	// Load or generate private key
	signer, err := loadPrivateKey()
	if err != nil {
		log.Fatalf("could not load private key from storage: %s", err)
	}

	// Export keys to bytes
	privKey, err := signer.MarshalBinary()
	if err != nil {
		log.Fatalf("could not export public key: %s", err)
	}
	pubKey, err := signer.GetUnsigner().MarshalBinary()
	if err != nil {
		log.Fatalf("could not export public key: %s", err)
	}

	hospitalPrivateKey = privKey
	hospitalPublicKey = pubKey

	// Create service discovery backed by ZooKeeper
	zkAddr := os.Getenv("ZK_ADDR")
	sd, err := NewZkServiceDiscovery(zkAddr, keyPrefix, leaseExpiry)
	if err != nil {
		log.Fatal(err)
	}
	serviceDiscovery = sd

	// Prepare register value
	registeredTime = time.Now()
	value := RegisterValue{
		Id:             hospitalId,
		Name:           hospitalName,
		GatewayAddr:    hospitalGatewayAddr,
		PublicKey:      hospitalPublicKey,
		RegisteredTime: registeredTime.Unix(),
	}

	// Register ourselves on service discovery
	if err := serviceDiscovery.Register(ctx, value); err != nil {
		log.Fatal(err)
	}

	// Create gRPC server
	lis, err := net.Listen("tcp", grpcListenAddr)
	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}
	grpcServer := grpc.NewServer()
	RegisterHospitalDiscoveryServer(grpcServer, NewServer(sd))

	// Register signal handlers
	done := make(chan bool)
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, os.Interrupt, syscall.SIGTERM)

	go func() {
		<-quit
		log.Println("Shutting down.")

		// Stop gRPC server
		grpcServer.GracefulStop()

		log.Println("gRPC server shut down gracefully.")

		// Cancel root context
		cancelFunc()

		// Revoke lease
		if err := serviceDiscovery.Revoke(context.Background()); err != nil {
			log.Println(err)
		}
		log.Println("Revoked lease.")

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

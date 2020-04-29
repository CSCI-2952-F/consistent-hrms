package main

import (
	"log"
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"

	"google.golang.org/grpc"

	"discovery"
)

var (
	keyPrefix string
)

func main() {
	// Configuration environment variables
	grpcListenAddr := os.Getenv("GRPC_LISTEN_ADDR")
	keyPrefix = os.Getenv("KEY_PREFIX")

	// Create service discovery backed by ZooKeeper
	zkAddr := os.Getenv("ZK_ADDR")
	sd, err := discovery.NewZkServiceDiscovery(zkAddr, keyPrefix, 5*time.Second)
	if err != nil {
		log.Fatalf("cannot start ZooKeeper ServiceDiscovery: %s", err)
	}

	// Create server
	server := NewServer(sd)

	// Create gRPC server
	lis, err := net.Listen("tcp", grpcListenAddr)
	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}
	grpcServer := grpc.NewServer()
	discovery.RegisterHospitalDiscoveryServer(grpcServer, server)

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

		close(done)
	}()

	// Start gRPC server
	log.Printf("Starting gRPC server on %s.\n", grpcListenAddr)
	if err := grpcServer.Serve(lis); err != nil {
		log.Fatal(err)
	}

	<-done
	log.Println("Shutdown completed.")
}

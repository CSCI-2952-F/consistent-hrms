package main

import (
	"log"
	"net"
	"os"
	"os/signal"
	"syscall"

	"google.golang.org/grpc"
)

var discoveryClient *DiscoverySvcClient

func main() {
	var err error

	// Parse environment variables
	grpcListenAddr := os.Getenv("GRPC_LISTEN_ADDR")
	discoveryGrpcAddr := os.Getenv("DISCOVERY_GRPC_ADDR")
	dsn := os.Getenv("SQL_DSN")

	// Create discovery service client
	discoveryClient, err = NewDiscoverySvcClient(discoveryGrpcAddr)
	if err != nil {
		log.Fatal(err)
	}

	// Create server
	server, err := NewServer(dsn)
	if err != nil {
		log.Fatalf("could not create server: %s", err)
	}

	log.Printf("Created server.")

	// Create gRPC server
	lis, err := net.Listen("tcp", grpcListenAddr)
	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}
	grpcServer := grpc.NewServer()
	RegisterCentralConsistentStorageServer(grpcServer, server)

	// Register signal handlers
	done := make(chan bool)
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, os.Interrupt, syscall.SIGTERM)

	go func() {
		<-quit
		log.Println("Shutting down...")

		// Stop gRPC server
		grpcServer.GracefulStop()
		log.Println("gRPC server shut down gracefully.")

		// Close server
		if err := server.Close(); err != nil {
			log.Printf("error while closing server: %s\n", err)
		}

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

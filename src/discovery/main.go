package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"

	etcd3 "go.etcd.io/etcd/clientv3"
	"google.golang.org/grpc"
)

var (
	hospitalId    string
	hospitalName  string
	etcdKeyPrefix string
	leaseExpiry   = 2 * time.Minute
)

type EtcdValue struct {
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
	etcdKeyPrefix = os.Getenv("ETCD_KEY_PREFIX")
	expiryEnv := os.Getenv("ETCD_LEASE_EXPIRY")
	if expiryEnv != "" {
		expiry, err := time.ParseDuration(expiryEnv)
		if err != nil {
			log.Fatalf("Could not parse expiry: %s", err)
		}
		leaseExpiry = expiry
	}

	// Create etcd client
	etcd, err := etcd3.New(etcd3.Config{
		Endpoints:   []string{etcdAddr},
		DialTimeout: 10 * time.Second,
	})
	if err != nil {
		log.Fatal(err)
	}

	// Register ourselves on etcd
	leaseID, err := register(ctx, etcd)
	if err != nil {
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
		if err := revoke(context.Background(), leaseID, etcd); err != nil {
			log.Println(err)
		}

		close(done)
	}()

	// Continuously renew the lease in the background
	go renew(ctx, leaseID, 5*time.Second, etcd)

	// Start gRPC server
	log.Printf("Starting gRPC server on %s.\n", grpcListenAddr)
	if err := grpcServer.Serve(lis); err != nil {
		log.Fatal(err)
	}

	<-done
	log.Println("Shutdown completed.")
}

func register(ctx context.Context, etcd *etcd3.Client) (leaseID etcd3.LeaseID, err error) {
	// Grant a new etcd lease
	grant, err := etcd.Grant(ctx, int64(leaseExpiry.Seconds()))
	if err != nil {
		err = fmt.Errorf("could not grant lease: %s\n", err)
		return
	}

	leaseID = grant.ID

	// Key is prefix + hospital ID
	key := etcdKeyPrefix + hospitalId

	// Store various information in etcd
	etcdValue := EtcdValue{
		Id:             hospitalId,
		Name:           hospitalName,
		RegisteredTime: time.Now().Unix(),
	}

	bytes, err := json.Marshal(etcdValue)
	if err != nil {
		panic(err)
	}

	// Register ourselves on etcd
	if _, e := etcd.Put(ctx, key, string(bytes), etcd3.WithLease(leaseID)); e != nil {
		err = fmt.Errorf("could not PUT in etcd: %s\n", e)
		return
	}

	return leaseID, nil
}

func renew(ctx context.Context, leaseID etcd3.LeaseID, duration time.Duration, etcd *etcd3.Client) {
	// Refresh lease in a ticker loop
	ticker := time.NewTicker(duration)
	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
		}

		if _, err := etcd.KeepAliveOnce(ctx, leaseID); err != nil {
			log.Printf("could not refresh lease: %s\n", err)
			continue
		}
	}
}

func revoke(ctx context.Context, leaseID etcd3.LeaseID, etcd *etcd3.Client) error {
	_, err := etcd.Revoke(ctx, leaseID)
	return err
}

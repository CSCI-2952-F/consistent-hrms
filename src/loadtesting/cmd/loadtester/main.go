package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"os"
	"os/signal"
	"strings"
	"syscall"

	"github.com/irvinlim/cs2952f-hrms/src/discovery"

	"github.com/irvinlim/cs2952f-hrms/src/loadtesting"
)

var (
	testName    string
	numRequests int
	requestRate int
)

func init() {
	flag.StringVar(&testName, "test", "", "Name of test to run")
	flag.IntVar(&numRequests, "n", 0, "Number of requests to send")
	flag.IntVar(&requestRate, "rate", 0, "Request rate to throttle sending of requests (in reqs/sec)")
}

func main() {
	flag.Parse()
	if testName == "" {
		flag.PrintDefaults()
		os.Exit(1)
	}

	ctx, cancelFunc := context.WithCancel(context.Background())

	// Get hospitals from discovery service
	discSvcClient, err := discovery.NewDiscoverySvcClient()
	if err != nil {
		log.Fatal(err)
	}
	hospitals, err := discSvcClient.GetHospitals(ctx)
	if err != nil {
		log.Fatal(err)
	}

	var hospitalIds []string
	for _, hospital := range hospitals {
		hospitalIds = append(hospitalIds, hospital.GetId())
	}

	fmt.Printf("Discovered hospitals: %s\n", strings.Join(hospitalIds, ", "))

	// Create new load test with a maximum number of open connections.
	test := loadtesting.NewLoadTest(hospitals, requestRate*3)

	// Register signal handlers
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, os.Interrupt, syscall.SIGTERM)
	go func() {
		<-quit
		log.Println("Stopping.")
		cancelFunc()
	}()

	// Set parameters
	test.SetRequestRate(requestRate)

	// Run test!
	result, err := test.Run(ctx, testName, numRequests)
	if err != nil {
		log.Fatalf("Error running test: %s", err)
	}

	// Print results
	fmt.Printf("Time taken: %.4fs\n", result.ActualDuration.Seconds())
	avgTime := result.ActualDuration.Seconds() / float64(numRequests)
	fmt.Printf("Average time per request: %.6f\n", avgTime)
	fmt.Printf("QPS: %.4f\n", 1/avgTime)
	fmt.Println()

	fmt.Printf("Number of requests: %d\n", numRequests*len(hospitalIds))
	fmt.Printf("Number of valid responses: %d\n", result.NumOk)
	fmt.Printf("Number of successes: %d\n", result.NumSuccess)
	fmt.Println()

	avgInflightTime := result.TotalRequestDuration.Seconds() / float64(result.NumOk)
	fmt.Printf("Average in-flight time per request: %.6fs\n", avgInflightTime)
}

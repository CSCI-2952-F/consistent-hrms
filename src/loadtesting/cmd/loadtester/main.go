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

	// Create new load test
	test := loadtesting.NewLoadTest(hospitals)

	// Register signal handlers
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, os.Interrupt, syscall.SIGTERM)
	go func() {
		<-quit
		log.Println("Stopping.")
		cancelFunc()
	}()

	fmt.Println("Starting test.")

	// Set parameters
	test.SetRequestRate(requestRate)

	// Run test!
	result, err := test.Run(ctx, testName, numRequests)
	if err != nil {
		log.Fatalf("Error running test: %s", err)
	}

	// Print results
	fmt.Printf("Time taken: %.4fs\n", result.ActualDuration.Seconds())
	fmt.Println()

	fmt.Printf("Number of requests: %d\n", numRequests*len(hospitalIds))
	fmt.Printf("Number of valid responses: %d\n", result.NumOk)
	fmt.Printf("Number of successes: %d\n", result.NumSuccess)
	fmt.Println()

	avgTime := result.TotalRequestDuration.Seconds() / float64(result.NumOk)
	qps := 1 / avgTime
	fmt.Printf("Total request elapsed time: %.2fs\n", result.TotalRequestDuration.Seconds())
	fmt.Printf("Average time taken per request: %.6fs\n", avgTime)
	fmt.Printf("Queries per second: %.2f QPS\n", qps)
}

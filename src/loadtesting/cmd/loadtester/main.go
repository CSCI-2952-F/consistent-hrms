package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"

	"github.com/irvinlim/cs2952f-hrms/src/discovery"
	"github.com/irvinlim/cs2952f-hrms/src/loadtesting"
)

var (
	testName    string
	numRequests int
)

func init() {
	flag.StringVar(&testName, "test", "", "Name of test to run")
	flag.IntVar(&numRequests, "n", 0, "Number of requests to send")
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

	// Create new load test
	test := loadtesting.NewLoadTest()

	// Register signal handlers
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, os.Interrupt, syscall.SIGTERM)
	go func() {
		<-quit
		log.Println("Stopping.")
		cancelFunc()
	}()

	// Run test!
	result, err := test.Run(ctx, testName, numRequests, hospitals)
	if err != nil {
		log.Fatalf("Error running test: %s", err)
	}

	// Print results
	fmt.Printf("Time taken: %dms\n", result.ActualDuration.Milliseconds())
	fmt.Println()

	fmt.Printf("Number of requests: %d\n", numRequests)
	fmt.Printf("Number of valid responses: %d\n", result.NumOk)
	fmt.Printf("Number of successes: %d\n", result.NumSuccess)
	fmt.Println()

	avgTime := float64(result.TotalRequestDuration.Milliseconds()) / float64(result.NumOk)
	qps := 1 / avgTime
	fmt.Printf("Total request elapsed time: %dms\n", result.TotalRequestDuration.Milliseconds())
	fmt.Printf("Average time taken per request: %.6fms\n", avgTime)
	fmt.Printf("Queries per second: %.2f QPS\n", qps)
}

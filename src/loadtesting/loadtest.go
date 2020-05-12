package loadtesting

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"time"

	"github.com/irvinlim/cs2952f-hrms/src/discovery"
	lib "github.com/irvinlim/cs2952f-hrms/src/golang-lib"
)

type LoadTest struct {
	client    *http.Client
	recv      chan RequestResponse
	hospitals []*discovery.Hospital

	// Requests per second to send
	requestRate int
}

type LoadTestResult struct {
	NumRequests int
	NumOk       int
	NumSuccess  int

	ActualDuration       time.Duration
	TotalRequestDuration time.Duration
}

type RequestResponse struct {
	err       error
	timeTaken time.Duration
	success   bool
}

func NewLoadTest(hospitals []*discovery.Hospital, poolSize int) *LoadTest {
	client := &http.Client{}

	// Limit number of TCP sockets open to poolSize
	if poolSize > 0 {
		client.Transport = &http.Transport{
			MaxIdleConns:        poolSize,
			MaxIdleConnsPerHost: poolSize,
			MaxConnsPerHost:     poolSize,
		}
	}

	return &LoadTest{
		client:    client,
		recv:      make(chan RequestResponse),
		hospitals: hospitals,
	}
}

func (t *LoadTest) SetRequestRate(rate int) {
	t.requestRate = rate
}

func (t *LoadTest) Run(ctx context.Context, name string, numRequests int) (*LoadTestResult, error) {
	// Prepare result
	result := LoadTestResult{NumRequests: numRequests}

	// Start time
	var startTime time.Time

	var tick *time.Ticker
	if t.requestRate > 0 {
		tick = time.NewTicker(time.Second)
		defer tick.Stop()
	}

	// Number of requests sent in total (for measurement)
	var totalRequestsSent int

	// Number of requests sent in current tick
	var tickRequestsSent int

	// Load patient cards
	cards, err := lib.ParsePatientCards("/var/patient_cards")
	if err != nil {
		return nil, err
	}

	fmt.Printf("Loaded %d patient cards.\n", len(cards))

	// Make sure that we have enough patient cards
	if numRequests > len(cards) {
		return nil, fmt.Errorf("cannot make more requests than number of patient cards: %d", len(cards))
	}
	cards = cards[:numRequests]

	fmt.Println("Starting test.")

	// Handle test type
	switch name {
	case "get":
		fmt.Println("This test may return unsuccessful requests if the cards are not already PUT in the storage.")

		// Start timer
		startTime = time.Now()

		// Get random keys
		for _, card := range cards {
			data := map[string]string{
				"key": card.UUID(),
			}
			body, err := json.Marshal(data)
			if err != nil {
				return nil, err
			}

			for _, hospital := range t.hospitals {
				url := "http://" + hospital.ConsistentStorageAddr
				go t.request(ctx, "GET", url, body, "exists")

				tickRequestsSent++
				totalRequestsSent++

				// If throttling is enabled, wait until next timestep if limit reached
				if tick != nil && tickRequestsSent == t.requestRate {
					<-tick.C
					tickRequestsSent = 0
				}
			}
		}

	case "put":
		// Start timer
		startTime = time.Now()

		// Put random keys; but all hospitals try to put the same key at the same time.
		for _, card := range cards {
			publicKeyBytes, err := card.PublicKey.MarshalBinary()
			if err != nil {
				return nil, err
			}

			data := map[string]string{
				"key":   card.UUID(),
				"value": string(publicKeyBytes),
			}
			body, err := json.Marshal(data)
			if err != nil {
				return nil, err
			}

			for _, hospital := range t.hospitals {
				url := "http://" + hospital.ConsistentStorageAddr
				go t.request(ctx, "PUT", url, body, "ok")

				tickRequestsSent++
				totalRequestsSent++

				// If throttling is enabled, wait until next timestep if limit reached
				if tick != nil && tickRequestsSent == t.requestRate {
					<-tick.C
					tickRequestsSent = 0
				}
			}
		}

	case "transfer":
		fmt.Println("This test will fail if the cards are not already PUT in the storage.")

		// Start timer
		startTime = time.Now()

		for _, card := range cards {
			for i, hospital := range t.hospitals {
				data := map[string]string{
					"key":  card.UUID(),
					"dest": t.hospitals[(i+1)%len(t.hospitals)].Id, // Transfer it to the next hospital
				}
				body, err := json.Marshal(data)
				if err != nil {
					return nil, err
				}

				url := "http://" + hospital.ConsistentStorageAddr
				go t.request(ctx, "TRANSFER", url, body, "transferred")

				tickRequestsSent++
				totalRequestsSent++

				// If throttling is enabled, wait until next timestep if limit reached
				if tick != nil && tickRequestsSent == t.requestRate {
					<-tick.C
					tickRequestsSent = 0
				}
			}
		}

	case "remove":
		fmt.Println("This test will fail if the cards already exist in the storage.")

		// Start timer
		startTime = time.Now()

		for _, card := range cards {
			for _, hospital := range t.hospitals {
				data := map[string]string{
					"key": card.UUID(),
				}
				body, err := json.Marshal(data)
				if err != nil {
					return nil, err
				}

				url := "http://" + hospital.ConsistentStorageAddr
				go t.request(ctx, "REMOVE", url, body, "removed")

				tickRequestsSent++
				totalRequestsSent++

				// If throttling is enabled, wait until next timestep if limit reached
				if tick != nil && tickRequestsSent == t.requestRate {
					<-tick.C
					tickRequestsSent = 0
				}
			}
		}

	default:
		return nil, fmt.Errorf("invalid test name: %s", name)
	}

	// Wait to receive response
	for i := 0; i < totalRequestsSent; i++ {
		select {
		case val := <-t.recv:
			if val.err != nil {
				continue
			}

			result.NumOk++
			result.TotalRequestDuration += val.timeTaken

			if val.success {
				result.NumSuccess++
			}
		case <-ctx.Done():
			return nil, context.Canceled
		}
	}

	// Once done, stop timer.
	result.ActualDuration = time.Since(startTime)

	return &result, nil
}

func (t *LoadTest) request(ctx context.Context, method string, url string, body []byte, successFlag string) {
	// Prepare response
	res := RequestResponse{}
	defer func() { t.recv <- res }()

	// Initialize request
	req, err := http.NewRequestWithContext(ctx, method, url, bytes.NewBuffer(body))
	if err != nil {
		res.err = err
		return
	}

	// Time request
	start := time.Now()
	resp, err := t.client.Do(req)
	res.timeTaken = time.Since(start)
	if err != nil {
		res.err = err
		return
	}

	// Read response body
	respBody, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		res.err = err
		return
	}

	// Parse JSON body
	var data map[string]interface{}
	if err := json.Unmarshal(respBody, &data); err != nil {
		res.err = err
		return
	}

	// Check success flag
	success, ok := data[successFlag].(bool)
	if !ok {
		res.err = fmt.Errorf("%s cannot be unmarshaled as bool, value is %v", successFlag, data[successFlag])
		return
	}

	res.success = success
	return
}

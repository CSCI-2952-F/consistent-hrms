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
	"go.etcd.io/etcd/pkg/stringutil"
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

func NewLoadTest(hospitals []*discovery.Hospital) *LoadTest {
	return &LoadTest{
		client:    &http.Client{},
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
	startTime := time.Now()

	var tick *time.Ticker
	if t.requestRate > 0 {
		tick = time.NewTicker(time.Second)
		defer tick.Stop()
	}

	// Number of requests sent in current tick
	var tickRequestsSent int

	// Handle test type
	switch name {
	case "get":
		// Get random keys
		for _, key := range randomKeys(numRequests) {
			data := map[string]string{
				"key": key,
			}
			body, err := json.Marshal(data)
			if err != nil {
				return nil, err
			}

			for _, hospital := range t.hospitals {
				url := "http://" + hospital.ConsistentStorageAddr
				go t.request(ctx, "GET", url, body, "exists")

				tickRequestsSent++

				// If throttling is enabled, wait until next timestep if limit reached
				if tick != nil && tickRequestsSent == t.requestRate {
					<-tick.C
					tickRequestsSent = 0
				}
			}
		}

	case "put":
		// Generate public key
		stub := KeyStorageStub{}
		key, err := lib.GeneratePrivateKey(&stub)
		if err != nil {
			return nil, fmt.Errorf("cannot generate key: %s", err)
		}
		pubKey := key.GetUnsigner()
		pubKeyBytes, err := pubKey.MarshalBinary()
		if err != nil {
			return nil, fmt.Errorf("cannot marshal key: %s", err)
		}

		// Put random keys; but all hospitals try to put the same key at the same time.
		for _, key := range randomKeys(numRequests) {
			data := map[string]string{
				"key":   key,
				"value": string(pubKeyBytes),
			}
			body, err := json.Marshal(data)
			if err != nil {
				return nil, err
			}

			for _, hospital := range t.hospitals {
				url := "http://" + hospital.ConsistentStorageAddr
				go t.request(ctx, "PUT", url, body, "ok")

				tickRequestsSent++

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
	for i := 0; i < numRequests*len(t.hospitals); i++ {
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

func randomKeys(n int) []string {
	return stringutil.RandomStrings(32, n)
}

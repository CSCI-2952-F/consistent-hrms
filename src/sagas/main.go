package main

import (
	"fmt"
	"log"
	"net"
	"os"
	"os/signal"
	"strconv"
	"sync"
	"syscall"

	"github.com/google/uuid"
	"google.golang.org/grpc"
	"gopkg.in/confluentinc/confluent-kafka-go.v1/kafka"
)

var (
	topicName string
	groupId   string
	storage   PersistentStorage
	producer  *kafka.Producer
	consumer  *kafka.Consumer

	// Mapping of partition to results by offset.
	resultChans []map[kafka.Offset]chan SagaResult
	resultMtx   []*sync.Mutex
)

func main() {
	// Parse environment variables
	topicName = os.Getenv("TOPIC_NAME")
	if topicName == "" {
		log.Fatalf("TOPIC_NAME not set")
	}
	num, err := strconv.ParseInt(os.Getenv("NUM_PARTITIONS"), 10, 32)
	if err != nil {
		log.Fatalf("NUM_PARTITIONS is not a valid integer")
	}
	numPartitions := int(num)
	if numPartitions <= 0 {
		log.Fatalf("NUM_PARTITIONS must be a positive integer")
	}
	brokers := os.Getenv("KAFKA_BROKERS")
	storageFilePath := os.Getenv("STORAGE_FILE_PATH")
	grpcListenAddr := os.Getenv("GRPC_LISTEN_ADDR")
	groupId = os.Getenv("GROUP_ID")

	// Initialize channels
	for i := 0; i < numPartitions; i++ {
		resultChans = append(resultChans, make(map[kafka.Offset]chan SagaResult))
		resultMtx = append(resultMtx, &sync.Mutex{})
	}

	// Initialize persistent storage
	s, err := NewFilePersistentStorage(storageFilePath)
	if err != nil {
		log.Fatalf("could not initialize storage: %v", err)
	}
	storage = s

	// Consumer group has to be unique within the topic.
	// We also use this to identify the producer of a message.
	// If not specified, generate and store it persistently.
	if groupId == "" {
		gid := storage.Get("group_id")
		if gid == nil {
			id := uuid.New()
			data, err := id.MarshalBinary()
			if err != nil {
				log.Fatal(err)
			}
			if err := storage.Put("group_id", data); err != nil {
				log.Fatal(err)
			}
			gid = data
		}
		groupId = string(gid)
	}

	defer closeKafka()

	// Create consumer
	consumer, err = kafka.NewConsumer(&kafka.ConfigMap{
		"bootstrap.servers":  brokers,
		"group.id":           groupId,
		"enable.auto.commit": false,
	})
	if err != nil {
		log.Fatalf("could not create consumer: %v", err)
	}

	// Create producer
	producer, err = kafka.NewProducer(&kafka.ConfigMap{
		"bootstrap.servers": brokers,
		"acks":              "all",
	})
	if err != nil {
		log.Fatalf("could not create producer: %v", err)
	}

	// Subscribe consumer to topic
	if err := consumer.Subscribe(topicName, nil); err != nil {
		log.Fatal(err)
	}

	// Create gRPC server
	lis, err := net.Listen("tcp", grpcListenAddr)
	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}
	grpcServer := grpc.NewServer()
	RegisterSagasConsistentStorageServer(grpcServer, &sagasConsistentStorageServer{})

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

		// Flush producer with a maximum timeout of 15 seconds
		producer.Flush(15 * 1000)

		// Close consumer and producer
		closeKafka()

		close(done)
	}()

	// Start polling in background
	go pollConsumer(consumer)

	// Start gRPC server
	log.Printf("Starting gRPC server on %s.\n", grpcListenAddr)
	if err := grpcServer.Serve(lis); err != nil {
		log.Fatal(err)
	}

	<-done
	log.Println("Shutdown completed.")
}

func closeKafka() {
	if producer != nil {
		producer.Close()
		producer = nil
	}
	if consumer != nil {
		if err := consumer.Close(); err != nil {
			fmt.Println(err)
		}
		consumer = nil
	}
}

func pollConsumer(c *kafka.Consumer) {
	for {
		msg, err := c.ReadMessage(-1)
		if err != nil {
			fmt.Printf("Consumer error: %v (%v)\n", err, msg)
			continue
		}

		partition := msg.TopicPartition.Partition
		offset := msg.TopicPartition.Offset

		headers := make(map[string][]byte)
		for _, header := range msg.Headers {
			headers[header.Key] = header.Value
		}

		fmt.Printf("Consumed message: topicPartition=%s key=%s value=%s headers=%s\n", msg.TopicPartition,
			string(msg.Key), string(msg.Value), headers)

		meta := SagaMetadata{
			Offset: int64(msg.TopicPartition.Offset),
			Owner:  string(headers["owner"]),
		}

		// Get and store the result of processing this operation
		result := processOperation(string(msg.Key), msg.Value, meta)

		fmt.Printf("Result of operation: ok=%v\n", result.Ok)

		// Commit the offset consumed
		if _, err := consumer.CommitMessage(msg); err != nil {
			fmt.Printf("WARNING: Could not commit offset: %v\n", err)
		}

		// Create result channel if not yet created
		resultCh := getOrCreateResultChan(partition, offset)

		// Finally send result to channel.
		// This is a blocking send, but the producer goroutine should already be reading it.
		resultCh <- result
	}
}

func getOrCreateResultChan(partition int32, offset kafka.Offset) chan SagaResult {
	resultMtx[partition].Lock()
	defer resultMtx[partition].Unlock()

	resultCh, ok := resultChans[partition][offset]
	if !ok {
		// Channel doesn't yet exist, create it
		resultChans[partition][offset] = make(chan SagaResult)
		resultCh = resultChans[partition][offset]
	}

	return resultCh
}

func deleteResultChan(partition int32, offset kafka.Offset) {
	// TODO: Benchmark to see tradeoff in lock contention latency vs memory leak over time
	resultMtx[partition].Lock()
	defer resultMtx[partition].Unlock()
	delete(resultChans[partition], offset)
}

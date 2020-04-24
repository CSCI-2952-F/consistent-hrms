package main

import (
	"context"
	"fmt"
	"log"
	"net"
	"os"
	"os/signal"
	"strconv"
	"sync"
	"syscall"
	"time"

	"google.golang.org/grpc"
	"gopkg.in/confluentinc/confluent-kafka-go.v1/kafka"
)

var (
	numPartitions   int32
	topicName       string
	groupId         string
	storage         PersistentStorage
	producer        *Producer
	consumer        *Consumer
	discoveryClient *DiscoverySvcClient

	// Mapping of partition to results by offset.
	resultChans []map[kafka.Offset]chan SagaResult
	resultMtx   []*sync.Mutex

	// Cryptographic keys for signing Kafka messages
	privateKey Signer
)

func main() {
	ctx, cancelFunc := context.WithCancel(context.Background())

	// Parse environment variables
	topicName = os.Getenv("TOPIC_NAME")
	if topicName == "" {
		log.Fatalf("TOPIC_NAME not set")
	}
	num, err := strconv.ParseInt(os.Getenv("NUM_PARTITIONS"), 10, 32)
	if err != nil {
		log.Fatalf("NUM_PARTITIONS is not a valid integer")
	}
	numPartitions = int32(num)
	if numPartitions <= 0 {
		log.Fatalf("NUM_PARTITIONS must be a positive integer")
	}
	brokers := os.Getenv("KAFKA_BROKERS")
	storageFilePath := os.Getenv("STORAGE_FILE_PATH")
	grpcListenAddr := os.Getenv("GRPC_LISTEN_ADDR")
	discoveryGrpcAddr := os.Getenv("DISCOVERY_GRPC_ADDR")

	// Initialize channels
	var i int32
	for i = 0; i < numPartitions; i++ {
		resultChans = append(resultChans, make(map[kafka.Offset]chan SagaResult))
		resultMtx = append(resultMtx, &sync.Mutex{})
	}

	// Initialize persistent storage
	s, err := NewFilePersistentStorage(storageFilePath)
	if err != nil {
		log.Fatalf("could not initialize storage: %v", err)
	}
	storage = s

	// Create discovery service client
	discoveryClient, err = NewDiscoverySvcClient(discoveryGrpcAddr)
	if err != nil {
		log.Fatal(err)
	}

	// Use the discovery service to get our unique ID as our consumer group ID.
	info, err := discoveryClient.GetInfo()
	if err != nil {
		log.Fatalf("could not lookup discovery svc: %s", err)
	}

	if info.Hospital.Id == "" {
		log.Fatal("discovery svc returned empty hospital id")
	}

	// Use the retrieved hospital information as our unique group ID
	groupId = info.Hospital.Id
	log.Printf("Acquired unique group ID: %s\n", groupId)

	// Initialize private key for signing Kafka messages
	privateKey, err = loadPrivateKey()
	if err != nil {
		log.Fatalf("could not load private key: %s", err)
	}

	defer closeKafka()

	// Create consumer
	kafkaConsumer, err := kafka.NewConsumer(&kafka.ConfigMap{
		"bootstrap.servers":  brokers,
		"group.id":           groupId,
		"enable.auto.commit": "false",    // must commit after each consumer read
		"auto.offset.reset":  "earliest", // necessary so that new consumers will start from the beginning of the log
	})
	if err != nil {
		log.Fatalf("could not create consumer: %v", err)
	}
	consumer = &Consumer{kafkaConsumer}

	// Create producer
	kafkaProducer, err := kafka.NewProducer(&kafka.ConfigMap{
		"bootstrap.servers": brokers,
		"acks":              "all",
	})
	if err != nil {
		log.Fatalf("could not create producer: %v", err)
	}
	producer = &Producer{kafkaProducer}

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

		// Stop consumer
		cancelFunc()

		// Flush producer with a maximum timeout of 15 seconds
		producer.Flush(15 * 1000)

		// Close consumer and producer
		closeKafka()

		close(done)
	}()

	// Start polling in background
	go pollConsumer(ctx, consumer)

	// Produce broadcast message for public key; this blocks until we also receive it
	publicKey := privateKey.GetUnsigner()
	publicKeyBytes, err := publicKey.MarshalBinary()
	if err != nil {
		log.Fatal(err)
	}
	if _, _, err := produce(SetPublicKeyOperation, nil, publicKeyBytes, ""); err != nil {
		log.Fatalf("could not produce initial message SetPublicKeyOperation")
	}

	log.Printf("Announced public key.")

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

func pollConsumer(ctx context.Context, c *Consumer) {
	// Keep polling for messages every second to also act as a heartbeat
	// to prevent being kicked from consumer group
	msgChan := c.ReadC(ctx, 1*time.Second)

	for {
		msg, ok := <-msgChan
		if !ok {
			log.Printf("Consumer stopped polling.")
			return
		}

		partition := msg.TopicPartition.Partition
		offset := msg.TopicPartition.Offset

		headers := make(map[string][]byte)
		for _, header := range msg.Headers {
			headers[header.Key] = header.Value
		}

		opTypeBytes, ok := headers["operation"]
		if !ok || len(opTypeBytes) != 1 {
			fmt.Printf("Message did not have valid operationType. topicPartition=%s op=%v\n", msg.TopicPartition,
				opTypeBytes)
			continue
		}

		// Parse operation type
		opType := SagaOperationType(opTypeBytes[0])

		meta := SagaMetadata{
			Partition: msg.TopicPartition.Partition,
			Offset:    int64(msg.TopicPartition.Offset),
			Owner:     string(headers["owner"]),
		}

		op := SagaOperation{
			operationType: opType,
			metadata:      meta,
			key:           string(msg.Key),
			value:         msg.Value,
			signature:     headers["signature"],
		}

		if hdr, ok := headers["newOwner"]; ok {
			op.newOwner = string(hdr)
		}

		fmt.Printf("Consumed message: %s\n", op)

		// Get and store the result of processing this operation
		result := op.process()

		fmt.Printf("Result of operation: ok=%v\n", result.Ok)

		// Commit the offset consumed
		if _, err := consumer.CommitMessage(msg); err != nil {
			fmt.Printf("WARNING: Could not commit offset: %v\n", err)
		}

		// Create result channel if not yet created
		resultCh := getOrCreateResultChan(partition, offset)

		// Finally send result to channel.
		resultCh <- result
	}
}

func getOrCreateResultChan(partition int32, offset kafka.Offset) chan SagaResult {
	resultMtx[partition].Lock()
	defer resultMtx[partition].Unlock()

	resultCh, ok := resultChans[partition][offset]
	if !ok {
		// Make channel buffered to prevent blocking sends
		resultChans[partition][offset] = make(chan SagaResult, 1)
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

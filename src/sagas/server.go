package main

import (
	"context"
	"fmt"
	"log"

	"gopkg.in/confluentinc/confluent-kafka-go.v1/kafka"
)

type sagasConsistentStorageServer struct{}

func (s *sagasConsistentStorageServer) Get(_ context.Context, r *GetRequest) (*GetResponse, error) {
	log.Printf("Received Get request: %v\n", r)

	// Retrieve from storage
	val, err := storage.Retrieve(r.Key)
	if err != nil {
		return nil, err
	}

	resp := &GetResponse{
		Exists: val.Value == nil,
		Value:  val.Value,
	}

	return resp, nil
}

func (s *sagasConsistentStorageServer) Put(_ context.Context, r *PutRequest) (*PutResponse, error) {
	log.Printf("Received Put request: %v\n", r)

	// Produce to Kafka
	partition, offset, err := produce([]byte(r.Key), r.Value)
	if err != nil {
		return nil, err
	}

	// Perform blocking read from results channel
	result := <-getOrCreateResultChan(partition, offset)

	// Clean up channel
	deleteResultChan(partition, offset)

	// Check if it was an Ok result
	if !result.Ok {
		resp := &PutResponse{
			Ok:        false,
			ErrorType: PutError_PUT_KEY_EXISTS,
			ErrorMsg:  fmt.Sprintf("key already exists, owner is %s", result.Value.Metadata.Owner),
		}
		return resp, nil
	}

	return &PutResponse{Ok: true}, nil
}

func (s *sagasConsistentStorageServer) Remove(_ context.Context, r *RemoveRequest) (*RemoveResponse, error) {
	log.Printf("Received Remove request: %v\n", r)

	// Produce to Kafka
	partition, offset, err := produce([]byte(r.Key), nil)
	if err != nil {
		return nil, err
	}

	// Perform blocking read from results channel
	result := <-getOrCreateResultChan(partition, offset)

	// Clean up channel
	deleteResultChan(partition, offset)

	if !result.Ok {
		resp := &RemoveResponse{Removed: false}
		if result.Value.Value == nil {
			resp.ErrorType = RemoveError_REMOVE_KEY_ERROR
			resp.ErrorMsg = "key does not exist"
		} else {
			resp.ErrorType = RemoveError_REMOVE_NOT_OWNER
			resp.ErrorMsg = fmt.Sprintf("not owner for key, owner is %s", result.Value.Metadata.Owner)
		}
		return resp, nil
	}

	return &RemoveResponse{Removed: true}, nil
}

func produce(key []byte, val []byte) (partition int32, offset kafka.Offset, err error) {
	msg := &kafka.Message{
		TopicPartition: kafka.TopicPartition{
			Topic:     &topicName,
			Partition: kafka.PartitionAny,
		},
		Key:     key,
		Value:   val,
		Headers: []kafka.Header{{Key: "owner", Value: []byte(groupId)}},
	}

	// Publish message to Kafka synchronously
	produced := make(chan kafka.Event)
	if e := producer.Produce(msg, produced); e != nil {
		err = fmt.Errorf("could not Produce message: %s", e)
		return
	}

	// Wait for delivery report and get (partition, offset)
	event := <-produced
	switch ev := event.(type) {
	case *kafka.Message:
		if ev.TopicPartition.Error != nil {
			err = fmt.Errorf("delivery error: %s", ev.TopicPartition.Error)
			return
		}

		return ev.TopicPartition.Partition, ev.TopicPartition.Offset, nil
	default:
		err = fmt.Errorf("unexpected Event type: %v", ev)
		return
	}
}

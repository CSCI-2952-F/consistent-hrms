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
	if val == nil {
		return &GetResponse{}, nil
	}

	resp := &GetResponse{
		Exists:  val.Value != nil,
		Value:   val.Value,
		IsOwner: val.Metadata.Owner == groupId,
		Owner:   val.Metadata.Owner,
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

	log.Printf("Produced to Kafka: partition=%d offset=%s\n", partition, offset)

	// Perform blocking read from results channel
	result := <-getOrCreateResultChan(partition, offset)

	// Clean up channel
	deleteResultChan(partition, offset)

	// Check if it was an Ok result
	if !result.Ok {
		resp := &PutResponse{
			Ok:    false,
			Owner: result.Value.Metadata.Owner,
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
		} else {
			resp.ErrorType = RemoveError_REMOVE_NOT_OWNER
		}
		return resp, nil
	}

	return &RemoveResponse{Removed: true}, nil
}

func (s *sagasConsistentStorageServer) Transfer(context.Context, *TransferRequest) (*TransferResponse, error) {
	panic("implement me")
}

func produce(key []byte, val []byte) (partition int32, offset kafka.Offset, err error) {
	msg := &kafka.Message{
		TopicPartition: kafka.TopicPartition{
			Topic:     &topicName,
			Partition: computePartition(key, numPartitions),
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

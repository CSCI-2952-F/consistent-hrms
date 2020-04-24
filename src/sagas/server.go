package main

import (
	"context"
	"fmt"
	"log"

	"gopkg.in/confluentinc/confluent-kafka-go.v1/kafka"
)

type sagasConsistentStorageServer struct{}

func (s *sagasConsistentStorageServer) Get(_ context.Context, r *GetRequest) (*GetResponse, error) {
	log.Printf("Received Get request: key=%s\n", r.Key)

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
	log.Printf("Received Put request: key=%s\n", r.Key)

	// Produce to Kafka
	partition, offset, err := produce(PutOperation, []byte(r.Key), r.Value, "")
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
			Ok:    false,
			Owner: result.Value.Metadata.Owner,
		}
		return resp, nil
	}

	return &PutResponse{Ok: true}, nil
}

func (s *sagasConsistentStorageServer) Remove(_ context.Context, r *RemoveRequest) (*RemoveResponse, error) {
	log.Printf("Received Remove request: key=%s\n", r.Key)

	// Produce to Kafka
	partition, offset, err := produce(RemoveOperation, []byte(r.Key), nil, "")
	if err != nil {
		return nil, err
	}

	// Perform blocking read from results channel
	result := <-getOrCreateResultChan(partition, offset)

	// Clean up channel
	deleteResultChan(partition, offset)

	if !result.Ok {
		resp := &RemoveResponse{}
		if result.Value.Value == nil {
			resp.ErrorType = RemoveError_REMOVE_KEY_ERROR
		} else {
			resp.ErrorType = RemoveError_REMOVE_NOT_OWNER
		}
		return resp, nil
	}

	return &RemoveResponse{Removed: true}, nil
}

func (s *sagasConsistentStorageServer) Transfer(_ context.Context, r *TransferRequest) (*TransferResponse, error) {
	log.Printf("Received Transfer request: key=%s\n", r.Key)

	// Produce to Kafka
	partition, offset, err := produce(TransferOperation, []byte(r.Key), nil, r.NewOwner)
	if err != nil {
		return nil, err
	}

	// Perform blocking read from results channel
	result := <-getOrCreateResultChan(partition, offset)

	// Clean up channel
	deleteResultChan(partition, offset)

	if !result.Ok {
		resp := &TransferResponse{}
		if result.Value.Value == nil {
			resp.ErrorType = TransferError_TRANSFER_KEY_ERROR
		} else {
			resp.ErrorType = TransferError_TRANSFER_NOT_OWNER
		}
		return resp, nil
	}

	return &TransferResponse{Transferred: true}, nil
}

func produce(operation SagaOperationType, key []byte, val []byte, newOwner string) (partition int32, offset kafka.Offset, err error) {
	// Sign value with private key
	signature, e := privateKey.Sign(val)
	if e != nil {
		err = e
		return
	}

	// Prepare headers
	headers := []kafka.Header{
		{Key: "owner", Value: []byte(groupId)},
		{Key: "operation", Value: []byte{byte(operation)}},
		{Key: "signature", Value: signature},
	}

	if operation == TransferOperation {
		headers = append(headers, kafka.Header{
			Key:   "newOwner",
			Value: []byte(newOwner),
		})
	}

	msg := &kafka.Message{
		TopicPartition: kafka.TopicPartition{
			Topic:     &topicName,
			Partition: computePartition(key, numPartitions),
		},
		Key:     key,
		Value:   val,
		Headers: headers,
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

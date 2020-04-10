package main

import (
	"log"
)

type SagaValue struct {
	Value    []byte       `json:"value"`
	Metadata SagaMetadata `json:"meta"`
}

type SagaMetadata struct {
	Offset int64  `json:"offset"`
	Owner  string `json:"owner"`
}

type SagaResult struct {
	// Result of operation
	Ok bool

	// Value after operation (regardless if it was successful)
	Value SagaValue
}

// Returns a result of processing a saga operation.
func processOperation(key string, value []byte, meta SagaMetadata) SagaResult {
	// Retrieve existing data in storage
	val, err := storage.Retrieve(key)
	if err != nil {
		log.Fatalf("could not retrieve %s from storage: %s", key, err)
	}

	// Prepare new SagaValue for insertion into storage
	newVal := SagaValue{Value: value, Metadata: meta}

	// Guarantee: Only one owner can write to a given key.
	// Only store if no other value exists for key at this point.
	if val.Value == nil && value != nil {
		if err := storage.Store(key, newVal); err != nil {
			log.Fatalf("could not store %s into storage: %s", key, err)
		}
		return SagaResult{
			Ok:    true,
			Value: newVal,
		}
	}

	// Guarantee: Only the owner of a key can delete it
	// Only delete the key if it exists, and owner matches
	if val.Value != nil && value == nil && val.Metadata.Owner == groupId {
		if err := storage.Remove(key, meta); err != nil {
			log.Fatalf("could not remove %s from storage: %s", key, err)
		}
		return SagaResult{
			Ok:    true,
			Value: newVal,
		}
	}

	// Otherwise, the result is a failure.
	return SagaResult{
		Ok:    false,
		Value: val,
	}
}

package main

import (
	"fmt"
	"log"
)

type SagaOperationType int

//go:generate stringer -type=SagaOperationType
const (
	PutOperation SagaOperationType = iota
	RemoveOperation
	TransferOperation
	SetPublicKeyOperation
)

type SagaValue struct {
	Value    []byte       `json:"value"`
	Metadata SagaMetadata `json:"meta"`
}

func (val *SagaValue) String() string {
	return fmt.Sprintf("value=[%d bytes] metadata=[%s]", len(val.Value), val.Metadata)
}

func (val *SagaValue) isEmpty() bool {
	return val == nil || val.Value == nil
}

func (val SagaValue) checkOwnership(op SagaOperation) bool {
	// First level of check: Existing value's owner must match
	if val.Metadata.Owner != op.metadata.Owner {
		log.Printf("ownership check failed for %s: owner does not match", op)
		return false
	}

	// Load public key for supposed owner
	key, err := loadPublicKey(op.metadata.Owner)
	if err != nil {
		log.Printf("ownership check failed for %s: public key not found: %s", op, err)
		return false
	}

	// Verify signature of supposed owner
	if err := key.Unsign(op.value, op.signature); err != nil {
		log.Printf("ownership check failed for %s: signature not valid: %s", op, err)
		return false
	}

	return true
}

type SagaMetadata struct {
	Partition int32  `json:"partition"`
	Offset    int64  `json:"offset"`
	Owner     string `json:"owner"`
}

func (s SagaMetadata) String() string {
	return fmt.Sprintf("partition=%d offset=%d owner=%s", s.Partition, s.Offset, s.Owner)
}

type SagaOperation struct {
	operationType SagaOperationType
	key           string
	value         []byte
	newOwner      string
	metadata      SagaMetadata
	signature     []byte
}

func (op SagaOperation) String() string {
	str := fmt.Sprintf("op=%s key=%s value=[%d bytes] metadata=[%s]", op.operationType, op.key, len(op.value), op.metadata)
	if op.newOwner != "" {
		str += " newOwner=" + op.newOwner
	}

	return str
}

type SagaResult struct {
	// Result of operation
	Ok bool

	// Value after operation (regardless if it was successful)
	Value *SagaValue
}

// Processes a saga operation by operating on the persistent storage.
// Returns a result of the processing.
// Note that the state of the persistent storage for every client at a given timestep should be identical.
func (op SagaOperation) process() SagaResult {
	// Owner is announcing a new public key.
	// Remember and store the public key for future verification (linearizable).
	if op.operationType == SetPublicKeyOperation {
		if err := storage.HPut("public_keys", op.metadata.Owner, op.value); err != nil {
			log.Fatalf("could not hput public key for %s into storage: %s", op.metadata.Owner, err)
		}
		return SagaResult{Ok: true}
	}

	// Retrieve existing data in storage
	val, err := storage.Retrieve(op.key)
	if err != nil {
		log.Fatalf("could not retrieve %s from storage: %s", op.key, err)
	}

	switch op.operationType {
	case PutOperation:
		// Guarantee: Only one owner can write non-nil data to an empty key.
		// Only store if value is not empty, and no other value exists for key at this point or an existing value's owner matches.
		if op.value != nil && (val.isEmpty() || val.checkOwnership(op)) {
			// Prepare new value
			newVal := SagaValue{Value: op.value, Metadata: op.metadata}

			// Store in storage
			if err := storage.Store(op.key, newVal); err != nil {
				log.Fatalf("could not store %s into storage: %s", op.key, err)
			}

			return SagaResult{
				Ok:    true,
				Value: &newVal,
			}
		}

	case RemoveOperation:
		// Guarantee: Only the owner of a key can delete it.
		// Only delete the key if it exists, and owner matches.
		if !val.isEmpty() && val.checkOwnership(op) {
			// Remove from storage
			newVal, err := storage.Remove(op.key, op.metadata)
			if err != nil {
				log.Fatalf("could not remove %s from storage: %s", op.key, err)
			}

			return SagaResult{
				Ok:    true,
				Value: newVal,
			}
		}

	case TransferOperation:
		// Guarantee: Only the owner of a key can transfer it.
		// Only update the metadata of the key if it exists, and the owner matches.
		if !val.isEmpty() && val.checkOwnership(op) {
			// TODO: Maybe verify that new owner exists?
			//       We are only verifying that the original owner was the one who
			//       requested the transfer, not whether the new owner accepts it.
			//       If so, we need to actually use multiple sub-transactions (i.e. real sagas).

			// Update owner
			newMeta := op.metadata
			newMeta.Owner = op.newOwner
			newVal := SagaValue{Value: val.Value, Metadata: newMeta}

			// Store in storage
			if err := storage.Store(op.key, newVal); err != nil {
				log.Fatalf("could not store %s into storage: %s", op.key, err)
			}

			return SagaResult{
				Ok:    true,
				Value: &newVal,
			}
		}
	}

	// Otherwise, the result is a failure.
	return SagaResult{
		Ok:    false,
		Value: val,
	}
}

package main

import (
	"crypto/sha256"
	"encoding/binary"
)

func computePartition(key []byte, numPartitions int32) int32 {
	hash := sha256.New()
	sum := hash.Sum(key)
	intSum := binary.BigEndian.Uint32(sum)
	return int32(intSum) % numPartitions
}

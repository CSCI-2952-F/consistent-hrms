package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"os"
	"path"
)

type PersistentStorage interface {
	Get(key string) (value []byte)
	Put(key string, value []byte) error
	Retrieve(key string) (val *SagaValue, err error)
	Store(key string, val SagaValue) error
	Remove(key string, meta SagaMetadata) (val *SagaValue, err error)
	HGet(hash string, key string) (value []byte)
	HPut(hash string, key string, value []byte) error
	HDel(hash string, key string) error
}

// FilePersistentStorage is a key-value storage on the filesystem for storing already consistent data.
type FilePersistentStorage struct {
	filePath    string
	data        map[string][]byte
	hash        map[string]map[string][]byte
	hashRootKey string
}

func NewFilePersistentStorage(filePath string) (*FilePersistentStorage, error) {
	storage := &FilePersistentStorage{
		filePath:    filePath,
		data:        make(map[string][]byte),
		hash:        make(map[string]map[string][]byte),
		hashRootKey: "__hash__",
	}

	// Ensure that path exists
	err := os.MkdirAll(path.Base(filePath), os.ModePerm)
	if err != nil {
		return nil, err
	}

	// Ensure that file exists
	var file *os.File
	if _, err := os.Stat(filePath); os.IsNotExist(err) {
		f, err := os.Create(filePath)
		if err != nil {
			return nil, err
		}
		file = f
	} else {
		f, err := os.Open(filePath)
		if err != nil {
			return nil, err
		}
		file = f
	}

	defer func() {
		_ = file.Close()
	}()

	// Load contents of file into memory; if not a valid JSON file overwrite it
	data, err := ioutil.ReadAll(file)
	if err != nil {
		return nil, err
	}
	if err := json.Unmarshal(data, &storage.data); err != nil {
		fmt.Printf("could not load %s, recreating JSON file: %v\n", filePath, err)
		storage.data = make(map[string][]byte)
		data, err := json.Marshal(storage.data)
		if err != nil {
			return nil, err
		}
		if err := ioutil.WriteFile(filePath, data, os.ModePerm); err != nil {
			return nil, err
		}
	}

	return storage, nil
}

func (f *FilePersistentStorage) Get(key string) (value []byte) {
	val, ok := f.data[key]
	if !ok {
		return nil
	}
	return val
}

func (f *FilePersistentStorage) Put(key string, value []byte) error {
	var oldVal []byte
	var oldOk bool

	// Keep track of old data to rollback if required
	oldVal, oldOk = f.data[key]
	rollback := func() {
		if oldOk {
			f.data[key] = oldVal
		} else {
			delete(f.data, key)
		}
	}

	// Update in-memory data
	f.data[key] = value

	// Marshal JSON data
	data, err := json.Marshal(f.data)
	if err != nil {
		rollback()
		return err
	}

	// Update filesystem data
	if err := ioutil.WriteFile(f.filePath, data, os.ModePerm); err != nil {
		rollback()
		return err
	}

	return nil
}

func (f *FilePersistentStorage) Retrieve(key string) (val *SagaValue, err error) {
	// Get raw bytes
	data := f.Get(key)

	// Empty data
	if data == nil {
		return nil, nil
	}

	// Unmarshal data as SagaValue
	if e := json.Unmarshal(data, &val); e != nil {
		err = e
		return
	}

	return
}

func (f *FilePersistentStorage) Store(key string, val SagaValue) error {
	// Store SagaValue using native Put()
	data, err := json.Marshal(val)
	if err != nil {
		return err
	}
	return f.Put(key, data)
}

func (f *FilePersistentStorage) Remove(key string, meta SagaMetadata) (*SagaValue, error) {
	// Store nil value with metadata
	value := SagaValue{
		Value:    nil,
		Metadata: meta,
	}
	if err := f.Store(key, value); err != nil {
		return nil, err
	}
	return &value, nil
}

func (f *FilePersistentStorage) HGet(hash string, key string) (value []byte) {
	h, ok := f.hash[hash]
	if !ok {
		return nil
	}

	val, ok := h[key]
	if !ok {
		return nil
	}

	return val
}

func (f *FilePersistentStorage) HPut(hash string, key string, value []byte) error {
	var oldHashOk bool
	var oldKeyOk bool
	var oldVal []byte
	var h map[string][]byte

	h, oldHashOk = f.hash[hash]
	if !oldHashOk {
		f.hash[hash] = make(map[string][]byte)
		h = f.hash[hash]
	}

	oldVal, oldKeyOk = h[key]

	// Update hash value
	h[key] = value

	// Prepare rollback function in case of error
	rollback := func() {
		if !oldHashOk {
			delete(f.hash, hash)
		} else if !oldKeyOk {
			delete(h, key)
		} else {
			h[key] = oldVal
		}
	}

	// Commit hash
	if err := f.commitHash(); err != nil {
		rollback()
		return err
	}

	return nil
}

func (f *FilePersistentStorage) HDel(hash string, key string) error {
	var oldVal []byte

	// If hash doesn't exist, return.
	h, ok := f.hash[hash]
	if !ok {
		return nil
	}

	// If key doesn't exist, return.
	oldVal, ok = h[key]
	if !ok {
		return nil
	}

	// Otherwise, delete from hash.
	delete(h, key)

	// If hash is now empty, delete hash.
	if len(h) == 0 {
		delete(f.hash, hash)
	}

	// Prepare rollback function in case of error.
	rollback := func() {
		h, ok := f.hash[hash]
		if !ok {
			f.hash[hash] = make(map[string][]byte)
		}
		h[key] = oldVal
	}

	// Commit hash
	if err := f.commitHash(); err != nil {
		rollback()
		return err
	}

	return nil
}

func (f *FilePersistentStorage) commitHash() error {
	// Marshal hash into bytes
	hashData, err := json.Marshal(f.hash)
	if err != nil {
		return err
	}

	// Store the hash bytes into the root key using the lower-level Put abstraction
	if err := f.Put(f.hashRootKey, hashData); err != nil {
		return err
	}

	return nil
}

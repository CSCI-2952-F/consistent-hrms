package main

import (
	"encoding/json"
	"io/ioutil"
	"os"
	"path"
)

type PersistentStorage interface {
	Get(key string) (value []byte)
	Put(key string, value []byte) error
	Retrieve(key string) (val *SagaValue, err error)
	Store(key string, val SagaValue) error
	Remove(key string, meta SagaMetadata) error
}

// FilePersistentStorage is a key-value storage on the filesystem for storing already consistent data.
type FilePersistentStorage struct {
	filePath string
	data     map[string][]byte
}

func NewFilePersistentStorage(filePath string) (*FilePersistentStorage, error) {
	storage := &FilePersistentStorage{
		filePath: filePath,
		data:     make(map[string][]byte),
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
	if err := json.Unmarshal(data, storage.data); err != nil {
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
	var value SagaValue
	if e := json.Unmarshal(data, &val); e != nil {
		err = e
		return
	}

	return &value, nil
}

func (f *FilePersistentStorage) Store(key string, val SagaValue) error {
	// Store SagaValue using native Put()
	data, err := json.Marshal(val)
	if err != nil {
		return err
	}
	return f.Put(key, data)
}

func (f *FilePersistentStorage) Remove(key string, meta SagaMetadata) error {
	// Store nil value with metadata
	pv := SagaValue{
		Value:    nil,
		Metadata: meta,
	}
	return f.Store(key, pv)
}

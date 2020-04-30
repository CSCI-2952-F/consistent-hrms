package discovery

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"os"
	"path"

	lib "github.com/irvinlim/cs2952f-hrms/src/golang-lib"
)

type KeyStorage struct {
	filepath string
}

func NewKeyStorage(filepath string) (*KeyStorage, error) {
	// Ensure that path exists
	if err := os.MkdirAll(path.Dir(filepath), os.ModePerm); err != nil {
		return nil, fmt.Errorf("could not MkdirAll: %s", err)
	}

	// Create if it does not exist
	if _, err := os.Stat(filepath); os.IsNotExist(err) {
		if _, err := os.Create(filepath); err != nil {
			return nil, fmt.Errorf("could not Create: %s", err)
		}
	}

	return &KeyStorage{filepath: filepath}, nil
}

func (s *KeyStorage) GetPrivateKey() ([]byte, error) {
	return ioutil.ReadFile(s.filepath)
}

func (s *KeyStorage) PutPrivateKey(data []byte) error {
	return ioutil.WriteFile(s.filepath, data, os.ModePerm)
}

type NamedKeyStorage struct {
	directory string
}

func NewNamedKeyStorage(directory string) (*NamedKeyStorage, error) {
	// Ensure that path exists
	if err := os.MkdirAll(directory, os.ModePerm); err != nil {
		return nil, fmt.Errorf("could not MkdirAll: %s", err)
	}

	return &NamedKeyStorage{directory: directory}, nil
}

func (s *NamedKeyStorage) GetKey(name string) ([]byte, error) {
	filepath := path.Join(s.directory, name)
	if _, err := os.Stat(filepath); os.IsNotExist(err) {
		return nil, nil
	}

	return ioutil.ReadFile(filepath)
}

func (s *NamedKeyStorage) PutKey(name string, data []byte) error {
	filepath := path.Join(s.directory, name)
	return ioutil.WriteFile(filepath, data, os.ModePerm)
}

type KeyPairStorage struct {
	publicKeyStorage  lib.CryptoPublicKeyStorage
	privateKeyStorage *NamedKeyStorage
}

func NewKeyPairStorage(publicKeyStorage lib.CryptoPublicKeyStorage, directory string) (*KeyPairStorage, error) {
	privateKeyStorage, err := NewNamedKeyStorage(directory)
	if err != nil {
		return nil, err
	}

	return &KeyPairStorage{
		publicKeyStorage:  publicKeyStorage,
		privateKeyStorage: privateKeyStorage,
	}, nil
}

func (k *KeyPairStorage) GetKey(name string, public bool) (*Key, error) {
	var keyData []byte
	if public {
		data, err := k.publicKeyStorage.GetPublicKey(name)
		if err != nil {
			return nil, err
		}
		keyData = data
	} else {
		data, err := k.privateKeyStorage.GetKey(name)
		if err != nil {
			return nil, err
		}
		if data == nil {
			return nil, nil
		}
		keyData = data
	}

	if keyData == nil {
		return nil, nil
	}

	var key Key
	if err := json.Unmarshal(keyData, &key); err != nil {
		return nil, err
	}

	return &key, nil
}

func (k *KeyPairStorage) PutKey(key Key) error {
	data, err := json.Marshal(key)
	if err != nil {
		return err
	}

	if key.Public {
		return k.publicKeyStorage.PutPublicKey(key.Name, data)
	} else {
		return k.privateKeyStorage.PutKey(key.Name, data)
	}
}

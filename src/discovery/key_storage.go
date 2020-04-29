package discovery

import (
	"fmt"
	"io/ioutil"
	"os"
	"path"
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

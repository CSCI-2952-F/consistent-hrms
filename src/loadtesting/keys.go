package loadtesting

type KeyStorageStub struct {
	value []byte
}

func (k *KeyStorageStub) GetPrivateKey() ([]byte, error) {
	return k.value, nil
}

func (k *KeyStorageStub) PutPrivateKey(data []byte) error {
	k.value = data
	return nil
}

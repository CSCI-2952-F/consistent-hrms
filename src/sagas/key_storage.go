package main

type PersistentKeyStorage struct {
	storage PersistentStorage
}

func (p *PersistentKeyStorage) GetPrivateKey() ([]byte, error) {
	return p.storage.Get("private_key"), nil
}

func (p *PersistentKeyStorage) PutPrivateKey(data []byte) error {
	return p.storage.Put("private_key", data)
}

func (p *PersistentKeyStorage) GetPublicKey(name string) ([]byte, error) {
	return p.storage.HGet("public_keys", name), nil
}

func (p *PersistentKeyStorage) PutPublicKey(name string, data []byte) error {
	return p.storage.HPut("public_keys", name, data)
}

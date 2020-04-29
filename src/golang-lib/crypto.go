package golang_lib

// See: https://play.golang.org/p/bzpD7Pa9mr

import (
	"crypto"
	"crypto/rand"
	"crypto/rsa"
	"crypto/sha256"
	"crypto/x509"
	"encoding"
	"encoding/pem"
	"errors"
	"fmt"
	"log"
)

type CryptoKeyStorage interface {
	GetPrivateKey() ([]byte, error)
	PutPrivateKey(data []byte) error
	GetPublicKey(name string) ([]byte, error)
	PutPublicKey(name string, data []byte) error
}

// A Signer can create signatures that verify against a public key.
type Signer interface {
	// Sign returns raw signature for the given data.
	Sign(data []byte) ([]byte, error)
	// GetUnsigner returns the corresponding Unsigner for this private key.
	GetUnsigner() Unsigner
	encoding.BinaryMarshaler
}

// A Unsigner will verify against a public key.
type Unsigner interface {
	// Unsign returns an error if the signature does not match that of the data.
	Unsign(data []byte, sig []byte) error
	encoding.BinaryMarshaler
}

type rsaPublicKey struct {
	*rsa.PublicKey
}

type rsaPrivateKey struct {
	*rsa.PrivateKey
}

func (r *rsaPrivateKey) MarshalBinary() (data []byte, err error) {
	pemdata := pem.EncodeToMemory(
		&pem.Block{
			Type:  "RSA PRIVATE KEY",
			Bytes: x509.MarshalPKCS1PrivateKey(r.PrivateKey),
		},
	)
	return pemdata, nil
}

// Sign signs data with rsa-sha256
func (r *rsaPrivateKey) Sign(data []byte) ([]byte, error) {
	h := sha256.New()
	h.Write(data)
	d := h.Sum(nil)
	return rsa.SignPKCS1v15(rand.Reader, r.PrivateKey, crypto.SHA256, d)
}

func (r *rsaPrivateKey) GetUnsigner() Unsigner {
	return &rsaPublicKey{&r.PrivateKey.PublicKey}
}

func (r *rsaPublicKey) MarshalBinary() (data []byte, err error) {
	pemdata := pem.EncodeToMemory(
		&pem.Block{
			Type:  "RSA PUBLIC KEY",
			Bytes: x509.MarshalPKCS1PublicKey(r.PublicKey),
		},
	)
	return pemdata, nil
}

// Unsign verifies the message using a rsa-sha256 signature
func (r *rsaPublicKey) Unsign(message []byte, sig []byte) error {
	h := sha256.New()
	h.Write(message)
	d := h.Sum(nil)
	return rsa.VerifyPKCS1v15(r.PublicKey, crypto.SHA256, d, sig)
}

func newSignerFromKey(k *rsa.PrivateKey) (Signer, error) {
	return &rsaPrivateKey{k}, nil
}

func newUnsignerFromKey(k *rsa.PublicKey) (Unsigner, error) {
	return &rsaPublicKey{k}, nil
}

func LoadPrivateKey(storage CryptoKeyStorage) (Signer, error) {
	// Try to load private key, otherwise regenerate it
	bytes, err := storage.GetPrivateKey()
	if err != nil || bytes == nil {
		return generatePrivateKey(storage)
	}

	// Parse private key, otherwise regenerate it
	key, err := ParsePrivateKey(bytes)
	if err == nil {
		return key, nil
	}

	log.Printf("warning: private key stored is corrupt, regenerating")

	return generatePrivateKey(storage)
}

func LoadPublicKey(storage CryptoKeyStorage, key string) (Unsigner, error) {
	bytes, err := storage.GetPublicKey(key)
	if err != nil || bytes == nil {
		return nil, fmt.Errorf("could not load public key for %s", key)
	}

	return ParsePublicKey(bytes)
}

func generatePrivateKey(storage CryptoKeyStorage) (Signer, error) {
	key, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		return nil, err
	}

	pemdata := pem.EncodeToMemory(
		&pem.Block{
			Type:  "RSA PRIVATE KEY",
			Bytes: x509.MarshalPKCS1PrivateKey(key),
		},
	)

	if err := storage.PutPrivateKey(pemdata); err != nil {
		return nil, err
	}

	return newSignerFromKey(key)
}

func ParsePrivateKey(pemBytes []byte) (Signer, error) {
	block, _ := pem.Decode(pemBytes)
	if block == nil {
		return nil, errors.New("ssh: no key found")
	}

	switch block.Type {
	case "RSA PRIVATE KEY":
		key, err := x509.ParsePKCS1PrivateKey(block.Bytes)
		if err != nil {
			return nil, err
		}
		return newSignerFromKey(key)
	default:
		return nil, fmt.Errorf("ssh: unsupported key type %q", block.Type)
	}
}

func ParsePublicKey(pemBytes []byte) (Unsigner, error) {
	block, _ := pem.Decode(pemBytes)
	if block == nil {
		return nil, errors.New("ssh: no key found")
	}

	switch block.Type {
	case "RSA PUBLIC KEY":
		key, err := x509.ParsePKCS1PublicKey(block.Bytes)
		if err != nil {
			return nil, err
		}
		return newUnsignerFromKey(key)
	default:
		return nil, fmt.Errorf("ssh: unsupported key type %q", block.Type)
	}
}

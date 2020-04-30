package discovery

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"path"
	"strings"
	"time"

	"github.com/samuel/go-zookeeper/zk"
	"go.etcd.io/etcd/pkg/stringutil"
)

type ZkServiceDiscovery struct {
	client    *zk.Conn
	id        string
	eventChan <-chan zk.Event

	keyPrefix string
	kmsPrefix string

	znodePath    string
	authPassword string

	privateKeyStorage *ZkKeyStorage
	keyStorage        *KeyPairStorage
}

func NewZkServiceDiscovery(zkAddr string, keyPrefix string, leaseExpiry time.Duration) (*ZkServiceDiscovery, error) {
	// Create zookeeper client
	zkConn, eventChan, err := zk.Connect([]string{zkAddr}, leaseExpiry)
	if err != nil {
		return nil, err
	}

	// Prepare password for ZK Digest ACLs
	randomStrings := stringutil.RandomStrings(32, 1)
	password := randomStrings[0]

	// Prepare key storage
	zkKeyStorage := &ZkKeyStorage{Conn: zkConn, prefix: "/keys/"}
	keyPairStorage, err := NewKeyPairStorage(zkKeyStorage, "/etc/discovery/keys/") // TODO Make configurable
	if err != nil {
		return nil, err
	}

	return &ZkServiceDiscovery{
		client:            zkConn,
		keyPrefix:         keyPrefix,
		kmsPrefix:         zkKeyStorage.prefix,
		eventChan:         eventChan,
		authPassword:      password,
		keyStorage:        keyPairStorage,
		privateKeyStorage: zkKeyStorage,
	}, nil
}

func (z *ZkServiceDiscovery) SetID(id string) {
	z.id = id
	z.privateKeyStorage.id = id
}

func (z *ZkServiceDiscovery) Register(ctx context.Context, value RegisterValue) error {
	// Path is prefix + ID
	zkPath := path.Join(z.keyPrefix, z.id)

	// Marshal JSON
	bytes, err := json.Marshal(value)
	if err != nil {
		return err
	}

	var incrPath string
	paths := strings.Split(z.keyPrefix, "/")

	// Create Znodes for the key prefix
	for _, tok := range paths {
		incrPath = path.Join(incrPath, tok)
		_, err := z.client.Create("/"+incrPath, nil, 0, zk.WorldACL(zk.PermRead))
		if err != nil && err != zk.ErrNodeExists {
			return fmt.Errorf("could not create Znode at %s: %s", incrPath, err)
		}
	}

	// Authenticate here for subsequent uses
	if err := z.client.AddAuth("digest", []byte(fmt.Sprintf("%s:%s", z.id, z.authPassword))); err != nil {
		return err
	}

	// Create ACLs for our Znode: Read-only to world, all permissions to owner
	worldACL := zk.WorldACL(zk.PermRead)
	digestACL := zk.DigestACL(zk.PermAll, z.id, z.authPassword)
	acl := []zk.ACL{
		worldACL[0],
		digestACL[0],
	}

	// Create a Znode with the specified ACLs
	znodePath, err := z.client.Create(zkPath, bytes, zk.FlagEphemeral, acl)
	if err != nil {
		return fmt.Errorf("could not create Znode at %s: %s", zkPath, err)
	}

	log.Printf("Created ephemeral Znode at %s.\n", znodePath)

	z.znodePath = znodePath

	return nil
}

func (z *ZkServiceDiscovery) Renew(context.Context, time.Duration) {
	// No need to explicitly renew a lease, ephemeral Znodes help us with that.
}

func (z *ZkServiceDiscovery) Revoke(context.Context) error {
	return z.client.Delete(z.znodePath, -1)
}

func (z *ZkServiceDiscovery) ListValues(context.Context) ([]RegisterValue, error) {
	// Remove trailing slash if any
	prefix := path.Clean(z.keyPrefix)

	// Get children suffixes
	children, _, err := z.client.Children(prefix)
	if err != nil {
		return nil, fmt.Errorf("could not get children at %s: %s", prefix, err)
	}

	var values []RegisterValue

	for _, childPath := range children {
		fullPath := path.Join(z.keyPrefix, childPath)
		bytes, _, err := z.client.Get(fullPath)
		if err != nil {
			return nil, fmt.Errorf("could not get child Znode at %s: %s", fullPath, err)
		}

		var value RegisterValue
		if err := json.Unmarshal(bytes, &value); err != nil {
			return nil, err
		}

		values = append(values, value)
	}

	return values, nil
}

func (z *ZkServiceDiscovery) GetKey(_ context.Context, name string, public bool) (*Key, error) {
	return z.keyStorage.GetKey(name, public)
}

func (z *ZkServiceDiscovery) PutKey(_ context.Context, key Key) error {
	return z.keyStorage.PutKey(key)
}

func (z *ZkServiceDiscovery) ListPublicKeys(_ context.Context, id string) ([]Key, error) {
	keysPath := path.Join(z.kmsPrefix, id)
	children, _, err := z.client.Children(keysPath)
	if err == zk.ErrNoNode {
		return nil, nil
	}
	if err != nil {
		return nil, fmt.Errorf("could not get children at %s: %s", keysPath, err)
	}

	var keys []Key
	for _, child := range children {
		fullPath := path.Join(keysPath, child)
		bytes, _, err := z.client.Get(fullPath)
		if err != nil {
			return nil, fmt.Errorf("could not get child Znode at %s: %s", fullPath, err)
		}

		var key Key
		if err := json.Unmarshal(bytes, &key); err != nil {
			return nil, err
		}

		keys = append(keys, key)
	}

	return keys, nil
}

type ZkKeyStorage struct {
	*zk.Conn
	id     string
	prefix string
}

func (z *ZkKeyStorage) GetPublicKey(name string) ([]byte, error) {
	if z.id == "" {
		return nil, fmt.Errorf("id not set")
	}

	// Get from path
	zkPath := path.Join(z.prefix, z.id, name)
	bytes, _, err := z.Get(zkPath)
	if err != nil {
		return nil, err
	}

	return bytes, nil
}

func (z *ZkKeyStorage) PutPublicKey(name string, data []byte) error {
	if z.id == "" {
		return fmt.Errorf("id not set")
	}

	// Join prefix to name
	zkPath := path.Join(z.prefix, z.id, name)

	// Incrementally create Znodes up to path
	var incrPath string
	paths := strings.Split(zkPath, "/")
	for _, tok := range paths {
		incrPath = path.Join(incrPath, tok)
		// TODO: Does the permission from a parent Znode restrict others from writing here?
		_, err := z.Create("/"+incrPath, nil, 0, zk.WorldACL(zk.PermAll))
		if err != nil && err != zk.ErrNodeExists {
			return fmt.Errorf("could not create Znode at %s: %s", incrPath, err)
		}
	}

	// Put at path
	if _, err := z.Set(zkPath, data, -1); err != nil {
		return err
	}

	return nil
}

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
	keyPrefix string
	eventChan <-chan zk.Event

	znodePath    string
	authPassword string
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

	return &ZkServiceDiscovery{
		client:       zkConn,
		keyPrefix:    keyPrefix,
		eventChan:    eventChan,
		authPassword: password,
	}, nil
}

func (z *ZkServiceDiscovery) SetID(id string) {
	z.id = id
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
		_, err := z.client.Create("/"+incrPath, nil, 0, zk.WorldACL(zk.PermAll))
		if err != nil && err != zk.ErrNodeExists {
			return fmt.Errorf("could not create Znode at %s: %s", incrPath, err)
		}
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
		return nil, err
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

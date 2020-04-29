package discovery

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"time"

	etcd3 "go.etcd.io/etcd/clientv3"
)

type EtcdServiceDiscovery struct {
	etcd        *etcd3.Client
	leaseID     etcd3.LeaseID
	leaseExpiry time.Duration

	keyPrefix string
	id        string
}

func NewEtcdServiceDiscovery(etcdAddr string, keyPrefix string, id string, leaseExpiry time.Duration) (*EtcdServiceDiscovery, error) {
	etcd, err := etcd3.New(etcd3.Config{
		Endpoints:   []string{etcdAddr},
		DialTimeout: 10 * time.Second,
	})
	if err != nil {
		return nil, err
	}

	return &EtcdServiceDiscovery{
		etcd:        etcd,
		keyPrefix:   keyPrefix,
		id:          id,
		leaseExpiry: leaseExpiry,
	}, nil
}

func (sd *EtcdServiceDiscovery) Register(ctx context.Context, value RegisterValue) error {
	// Grant a new etcd lease
	grant, err := sd.etcd.Grant(ctx, int64(sd.leaseExpiry.Seconds()))
	if err != nil {
		return fmt.Errorf("could not grant lease: %s\n", err)
	}

	sd.leaseID = grant.ID

	// Key is prefix + hospital ID
	key := sd.keyPrefix + sd.id

	bytes, err := json.Marshal(value)
	if err != nil {
		return err
	}

	// Register ourselves on etcd
	if _, err := sd.etcd.Put(ctx, key, string(bytes), etcd3.WithLease(sd.leaseID)); err != nil {
		return fmt.Errorf("could not PUT in etcd: %s\n", err)
	}

	return nil
}

func (sd *EtcdServiceDiscovery) Renew(ctx context.Context, duration time.Duration) {
	// Refresh lease in a ticker loop
	ticker := time.NewTicker(duration)
	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
		}

		if _, err := sd.etcd.KeepAliveOnce(ctx, sd.leaseID); err != nil {
			log.Printf("could not refresh lease: %s\n", err)
			continue
		}
	}
}

func (sd *EtcdServiceDiscovery) Revoke(ctx context.Context) error {
	_, err := sd.etcd.Revoke(ctx, sd.leaseID)
	return err
}

func (sd *EtcdServiceDiscovery) ListValues(ctx context.Context) ([]RegisterValue, error) {
	// Get all keys with prefix
	etcdResp, err := sd.etcd.Get(ctx, sd.keyPrefix, etcd3.WithPrefix())
	if err != nil {
		return nil, err
	}

	var values []RegisterValue

	// Process etcd values
	for _, kv := range etcdResp.Kvs {
		// Unmarshal JSON
		var value RegisterValue
		if err := json.Unmarshal(kv.Value, &value); err != nil {
			log.Printf("Could not unmarshal %s: %s\n", string(kv.Key), err)
			log.Printf("Value of %s: %s\n", string(kv.Key), string(kv.Value))
			continue
		}

		values = append(values, value)
	}

	return values, nil
}

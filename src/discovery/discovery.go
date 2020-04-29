package discovery

import (
	"context"
	"time"
)

type ServiceDiscovery interface {
	Register(ctx context.Context, value RegisterValue) error
	Renew(ctx context.Context, duration time.Duration)
	Revoke(ctx context.Context) error
	ListValues(ctx context.Context) ([]RegisterValue, error)
}

type RegisterValue struct {
	Id                    string `json:"id"`
	Name                  string `json:"name"`
	GatewayAddr           string `json:"gateway_addr"`
	ConsistentStorageAddr string `json:"consistent_storage_addr"`
	PublicKey             []byte `json:"public_key"`
	RegisteredTime        int64  `json:"registered_time"`
}

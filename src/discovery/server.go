package main

import (
	"context"
	"encoding/json"
	"log"

	etcd3 "go.etcd.io/etcd/clientv3"
)

type Server struct {
	etcd *etcd3.Client
}

func NewServer(etcd *etcd3.Client) *Server {
	return &Server{etcd: etcd}
}

func (s *Server) ListHospitals(ctx context.Context, _ *ListRequest) (*ListResponse, error) {
	// Get all keys with prefix
	etcdResp, err := s.etcd.Get(ctx, etcdKeyPrefix, etcd3.WithPrefix())
	if err != nil {
		return nil, err
	}

	// Prepare ListResponse
	res := ListResponse{}

	// Process etcd values
	for _, kv := range etcdResp.Kvs {
		// Unmarshal JSON
		var etcdValue EtcdValue
		if err := json.Unmarshal(kv.Value, &etcdValue); err != nil {
			log.Printf("Could not unmarshal %s: %s\n", string(kv.Key), err)
			log.Printf("Value of %s: %s\n", string(kv.Key), string(kv.Value))
			continue
		}

		// Create gRPC response
		hospital := ListResponse_Hospital{
			Id:             etcdValue.Id,
			Name:           etcdValue.Name,
			RegisteredTime: etcdValue.RegisteredTime,
		}

		res.Hospitals = append(res.Hospitals, &hospital)
	}

	return &res, nil
}

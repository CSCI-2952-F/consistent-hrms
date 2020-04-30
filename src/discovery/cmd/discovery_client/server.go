package main

import (
	"context"

	"github.com/irvinlim/cs2952f-hrms/src/discovery"
)

type Server struct {
	sd discovery.ServiceDiscovery
}

func NewServer(sd discovery.ServiceDiscovery) *Server {
	return &Server{sd: sd}
}

func (s *Server) GetInfo(context.Context, *discovery.InfoRequest) (*discovery.InfoResponse, error) {
	res := discovery.InfoResponse{
		Id:             hospitalId,
		Name:           hospitalName,
		PrivateKey:     hospitalPrivateKey,
		RegisteredTime: registeredTime.Unix(),
	}

	return &res, nil
}

func (s *Server) ListHospitals(ctx context.Context, _ *discovery.ListRequest) (*discovery.ListResponse, error) {
	values, err := s.sd.ListValues(ctx)
	if err != nil {
		return nil, err
	}

	var hospitals []*discovery.Hospital

	for _, value := range values {
		// Fetch public keys
		publicKeys, err := s.sd.ListPublicKeys(ctx, value.Id)
		if err != nil {
			return nil, err
		}

		// Transform to proto
		var discoveryKeys []*discovery.DiscoveryKey
		for _, key := range publicKeys {
			dkey := &discovery.DiscoveryKey{
				Name:   key.Name,
				Value:  key.Value,
				Public: key.Public,
				Scheme: key.Scheme,
			}
			discoveryKeys = append(discoveryKeys, dkey)
		}

		hospital := discovery.Hospital{
			Id:                    value.Id,
			Name:                  value.Name,
			GatewayAddr:           value.GatewayAddr,
			ConsistentStorageAddr: value.ConsistentStorageAddr,
			PublicKey:             value.PublicKey,
			RegisteredTime:        value.RegisteredTime,
			PublicKeys:            discoveryKeys,
		}

		hospitals = append(hospitals, &hospital)
	}

	res := discovery.ListResponse{
		Hospitals: hospitals,
	}

	return &res, nil
}

func (s *Server) GetKey(ctx context.Context, request *discovery.GetKeyRequest) (*discovery.GetKeyResponse, error) {
	key, err := s.sd.GetKey(ctx, request.Name, request.Public)
	if err != nil {
		return nil, err
	}

	if key == nil {
		return &discovery.GetKeyResponse{Found: false}, nil
	}

	dkey := &discovery.DiscoveryKey{
		Name:   key.Name,
		Value:  key.Value,
		Public: key.Public,
		Scheme: key.Scheme,
	}

	return &discovery.GetKeyResponse{Found: true, Key: dkey}, nil
}

func (s *Server) PutKey(ctx context.Context, request *discovery.PutKeyRequest) (*discovery.PutKeyResponse, error) {
	key := discovery.Key{
		Name:   request.Key.Name,
		Value:  request.Key.Value,
		Public: request.Key.Public,
		Scheme: request.Key.Scheme,
	}

	if err := s.sd.PutKey(ctx, key); err != nil {
		return &discovery.PutKeyResponse{Ok: false, Error: err.Error()}, nil
	}

	return &discovery.PutKeyResponse{Ok: true}, nil
}

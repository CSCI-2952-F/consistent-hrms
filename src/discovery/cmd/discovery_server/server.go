package main

import (
	"context"
	"fmt"

	"discovery"
)

type Server struct {
	sd discovery.ServiceDiscovery
}

func NewServer(sd discovery.ServiceDiscovery) *Server {
	return &Server{sd: sd}
}

func (s *Server) GetInfo(context.Context, *discovery.InfoRequest) (*discovery.InfoResponse, error) {
	return nil, fmt.Errorf("cannot call GetInfo on discovery_server")
}

func (s *Server) ListHospitals(ctx context.Context, _ *discovery.ListRequest) (*discovery.ListResponse, error) {
	values, err := s.sd.ListValues(ctx)
	if err != nil {
		return nil, err
	}

	var hospitals []*discovery.Hospital

	for _, value := range values {
		hospital := discovery.Hospital{
			Id:             value.Id,
			Name:           value.Name,
			GatewayAddr:    value.GatewayAddr,
			PublicKey:      value.PublicKey,
			RegisteredTime: value.RegisteredTime,
		}

		hospitals = append(hospitals, &hospital)
	}

	res := discovery.ListResponse{
		Hospitals: hospitals,
	}

	return &res, nil
}

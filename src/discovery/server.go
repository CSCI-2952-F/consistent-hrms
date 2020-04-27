package main

import (
	"context"
)

type Server struct {
	sd ServiceDiscovery
}

func NewServer(sd ServiceDiscovery) *Server {
	return &Server{sd: sd}
}

func (s *Server) GetInfo(context.Context, *InfoRequest) (*InfoResponse, error) {
	res := InfoResponse{
		Id:             hospitalId,
		Name:           hospitalName,
		PrivateKey:     hospitalPrivateKey,
		RegisteredTime: registeredTime.Unix(),
	}

	return &res, nil
}

func (s *Server) ListHospitals(ctx context.Context, _ *ListRequest) (*ListResponse, error) {
	values, err := s.sd.ListValues(ctx)
	if err != nil {
		return nil, err
	}

	var hospitals []*Hospital

	for _, value := range values {
		hospital := Hospital{
			Id:             value.Id,
			Name:           value.Name,
			GatewayAddr:    value.GatewayAddr,
			PublicKey:      value.PublicKey,
			RegisteredTime: value.RegisteredTime,
		}

		hospitals = append(hospitals, &hospital)
	}

	res := ListResponse{
		Hospitals: hospitals,
	}

	return &res, nil
}

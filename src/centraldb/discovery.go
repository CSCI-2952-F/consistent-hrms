package main

import (
	"context"
	"errors"

	"google.golang.org/grpc"
)

type DiscoverySvcClient struct {
	client HospitalDiscoveryClient
}

func NewDiscoverySvcClient(grpcAddr string) (*DiscoverySvcClient, error) {
	conn, err := grpc.Dial(grpcAddr, grpc.WithInsecure())
	if err != nil {
		return nil, err
	}
	client := NewHospitalDiscoveryClient(conn)
	return &DiscoverySvcClient{
		client: client,
	}, nil
}

func (c *DiscoverySvcClient) GetPublicKey(ctx context.Context, id string) (Unsigner, error) {
	req := ListRequest{}
	resp, err := c.client.ListHospitals(ctx, &req)
	if err != nil {
		return nil, err
	}

	for _, hospital := range resp.Hospitals {
		if hospital.GetId() == id {
			key := hospital.GetPublicKey()
			return parsePublicKey(key)
		}
	}

	return nil, errors.New("hospital not found")
}

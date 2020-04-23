package main

import (
	"context"

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

func (c *DiscoverySvcClient) GetInfo() (*InfoResponse, error) {
	req := InfoRequest{}
	return c.client.GetInfo(context.Background(), &req)
}

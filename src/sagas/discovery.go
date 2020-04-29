package main

import (
	"context"
	"errors"
	"fmt"

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

func (c *DiscoverySvcClient) GetUniqueId() (string, error) {
	req := InfoRequest{}
	info, err := c.client.GetInfo(context.Background(), &req)
	if err != nil {
		return "", fmt.Errorf("could not lookup discovery svc: %s", err)
	}

	if info.Id == "" {
		return "", errors.New("discovery svc returned empty hospital id")
	}

	return info.Id, nil
}

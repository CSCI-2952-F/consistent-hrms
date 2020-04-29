package discovery

import (
	"context"
	"errors"
	"fmt"

	lib "github.com/irvinlim/cs2952f-hrms/src/golang-lib"
	"google.golang.org/grpc"
)

type DiscoverySvcClient struct {
	client HospitalDiscoveryClient
}

const DISCOVERY_GRPC_ADDR = "discovery_service:8080"

func NewDiscoverySvcClient() (*DiscoverySvcClient, error) {
	conn, err := grpc.Dial(DISCOVERY_GRPC_ADDR, grpc.WithInsecure())
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
	info, err := c.client.GetInfo(context.Background(), &req)
	if err != nil {
		return nil, fmt.Errorf("could not lookup discovery svc: %s", err)
	}

	return info, nil
}

func (c *DiscoverySvcClient) GetUniqueId() (string, error) {
	info, err := c.GetInfo()
	if err != nil {
		return "", fmt.Errorf("could not get info: %s", err)
	}

	if info.Id == "" {
		return "", errors.New("discovery svc returned empty hospital id")
	}

	return info.Id, nil
}

func (c *DiscoverySvcClient) GetHospitals(ctx context.Context) ([]*Hospital, error) {
	req := ListRequest{}
	resp, err := c.client.ListHospitals(ctx, &req)
	if err != nil {
		return nil, err
	}

	return resp.Hospitals, nil
}

func (c *DiscoverySvcClient) GetPublicKey(ctx context.Context, id string) (lib.Unsigner, error) {
	hospitals, err := c.GetHospitals(ctx)
	if err != nil {
		return nil, err
	}

	for _, hospital := range hospitals {
		if hospital.GetId() == id {
			key := hospital.GetPublicKey()
			return lib.ParsePublicKey(key)
		}
	}

	return nil, errors.New("hospital not found")
}

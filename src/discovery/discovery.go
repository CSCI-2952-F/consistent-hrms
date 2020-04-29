package discovery

import (
	"context"
	"errors"

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

func (c *DiscoverySvcClient) GetHospitals(ctx context.Context) ([]*Hospital, error) {
	req := ListRequest{}
	resp, err := c.client.ListHospitals(ctx, &req)
	if err != nil {
		return nil, err
	}

	return resp.Hospitals, nil
}

func (c *DiscoverySvcClient) GetPublicKey(ctx context.Context, id string) (Unsigner, error) {
	hospitals, err := c.GetHospitals(ctx)
	if err != nil {
		return nil, err
	}

	for _, hospital := range hospitals {
		if hospital.GetId() == id {
			key := hospital.GetPublicKey()
			return parsePublicKey(key)
		}
	}

	return nil, errors.New("hospital not found")
}

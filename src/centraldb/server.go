package main

import (
	"context"
	"database/sql"
	"errors"

	_ "github.com/go-sql-driver/mysql"
	"github.com/golang/protobuf/proto"
)

type Server struct {
	db *sql.DB
}

func NewServer(dsn string) (*Server, error) {
	// Open MySQL connection (lazily: see http://go-database-sql.org/accessing.html)
	db, err := sql.Open("mysql", dsn)
	if err != nil {
		return nil, err
	}

	// Create table if it doesn't exist
	if _, err := db.Exec(`CREATE TABLE IF NOT EXISTS patient_registrations (
		patient_id varchar(255) NOT NULL,
  		hospital_id varchar(255) NOT NULL,
  		PRIMARY KEY (patient_id)
	) ENGINE=InnoDB DEFAULT CHARSET=latin1;`); err != nil {
		_ = db.Close()
		return nil, err
	}

	return &Server{db: db}, nil
}

func (s *Server) Close() error {
	return s.db.Close()
}

func (s *Server) Get(ctx context.Context, request *GetRequest) (*GetResponse, error) {
	panic("implement me")
}

func (s *Server) Put(ctx context.Context, request *PutRequest) (*PutResponse, error) {
	panic("implement me")
}

func (s *Server) Remove(ctx context.Context, request *RemoveRequest) (*RemoveResponse, error) {
	panic("implement me")
}

func (s *Server) Transfer(ctx context.Context, request *TransferRequest) (*TransferResponse, error) {
	panic("implement me")
}

func (s *Server) Request(ctx context.Context, r *WrappedRequest) (*WrappedResponse, error) {
	// Look up requestor and get their public key
	publicKey, err := discoveryClient.GetPublicKey(ctx, r.Id)
	if err != nil {
		return nil, err
	}

	// Create verification method for wrapped request
	verify := func(msg proto.Message) error {
		// Marshal the wrapped request
		bytes, err := proto.Marshal(msg)
		if err != nil {
			return err
		}

		// Verify the request signature
		return publicKey.Unsign(bytes, r.Signature)
	}

	// Handle wrapped request and return wrapped response
	switch req := r.Request.(type) {
	case *WrappedRequest_Get:
		if err := verify(req.Get); err != nil {
			return nil, err
		}
		resp, err := s.Get(ctx, req.Get)
		if err != nil {
			return nil, err
		}
		return &WrappedResponse{Response: &WrappedResponse_Get{Get: resp}}, nil

	case *WrappedRequest_Put:
		if err := verify(req.Put); err != nil {
			return nil, err
		}
		resp, err := s.Put(ctx, req.Put)
		if err != nil {
			return nil, err
		}
		return &WrappedResponse{Response: &WrappedResponse_Put{Put: resp}}, nil

	case *WrappedRequest_Remove:
		if err := verify(req.Remove); err != nil {
			return nil, err
		}
		resp, err := s.Remove(ctx, req.Remove)
		if err != nil {
			return nil, err
		}
		return &WrappedResponse{Response: &WrappedResponse_Remove{Remove: resp}}, nil

	case *WrappedRequest_Transfer:
		if err := verify(req.Transfer); err != nil {
			return nil, err
		}
		resp, err := s.Transfer(ctx, req.Transfer)
		if err != nil {
			return nil, err
		}
		return &WrappedResponse{Response: &WrappedResponse_Transfer{Transfer: resp}}, nil
	}

	return nil, errors.New("invalid request")
}

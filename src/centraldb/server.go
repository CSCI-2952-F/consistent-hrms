package main

import (
	"context"
	"database/sql"
	"errors"
	"log"

	_ "github.com/go-sql-driver/mysql"
	"github.com/golang/protobuf/proto"
)

type Server struct {
	db *sql.DB
}

var ErrNilRequestorId = errors.New("nil requestor ID")

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
  		public_key text NOT NULL,
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
	var hospitalId, publicKey string
	exists := true

	// Get requestor's hospital ID
	id := ctx.Value("id").(string)
	if id == "" {
		return nil, ErrNilRequestorId
	}

	// Start transaction
	tx, err := s.db.Begin()
	if err != nil {
		return nil, err
	}

	// Find patient registrations matching the key with a read lock
	row := tx.QueryRowContext(ctx, `SELECT hospital_id, public_key FROM patient_registrations WHERE patient_id = ? FOR SHARE;`, request.Key)

	// Scan the row
	if err := row.Scan(&hospitalId, &publicKey); err != nil {
		if err != sql.ErrNoRows {
			_ = tx.Rollback()
			return nil, err
		}
		exists = false
	}

	// Commit the transaction
	if err := tx.Commit(); err != nil {
		return nil, err
	}

	// Prepare response
	resp := GetResponse{Exists: exists}
	if exists {
		resp.Value = []byte(publicKey)
		resp.Owner = hospitalId
		resp.IsOwner = hospitalId == id
	}

	return &resp, nil
}

func (s *Server) Put(ctx context.Context, request *PutRequest) (*PutResponse, error) {
	var hospitalId string
	exists := true

	// Get requestor's hospital ID
	id := ctx.Value("id").(string)
	if id == "" {
		return nil, ErrNilRequestorId
	}

	// Start transaction
	tx, err := s.db.Begin()
	if err != nil {
		return nil, err
	}

	// Check if there is an existing entry with a write lock
	row := tx.QueryRowContext(ctx, `SELECT hospital_id FROM patient_registrations WHERE patient_id = ? FOR UPDATE;`, request.Key)
	if err := row.Scan(&hospitalId); err != nil {
		if err != sql.ErrNoRows {
			_ = tx.Rollback()
			return nil, err
		}
		exists = false
	}

	// Fail if an existing entry exists but the owner does not match
	if exists && hospitalId != id {
		log.Printf("ownership mismatch for %s: %s does not match requestor id %s", request.Key, hospitalId, id)

		// Rollback transaction
		_ = tx.Rollback()

		// Return failure response
		resp := PutResponse{Owner: hospitalId, Ok: false}
		return &resp, nil
	}

	// Otherwise, either update or insert the entry.
	var res sql.Result
	if exists {
		res, err = tx.ExecContext(ctx, `UPDATE patient_registrations SET public_key = ? WHERE patient_id = ? AND hospital_id = ?;`, request.Value, request.Key, id)
		if err != nil {
			_ = tx.Rollback()
			return nil, err
		}
	} else {
		res, err = tx.ExecContext(ctx, `INSERT INTO patient_registrations (patient_id, hospital_id, public_key) VALUES (?, ?, ?);`, request.Key, id, request.Value)
		if err != nil {
			_ = tx.Rollback()
			return nil, err
		}
	}

	// Make sure that we updated/inserted a row
	rowsAffected, err := res.RowsAffected()
	if err != nil {
		_ = tx.Rollback()
		return nil, err
	}
	if rowsAffected != 1 {
		_ = tx.Rollback()
		return nil, errors.New("no rows updated")
	}

	// Commit the transaction
	if err := tx.Commit(); err != nil {
		return nil, err
	}

	// Prepare response
	resp := PutResponse{
		Ok:    true,
		Owner: id,
	}

	return &resp, nil
}

func (s *Server) Remove(ctx context.Context, request *RemoveRequest) (*RemoveResponse, error) {
	var hospitalId string
	exists := true

	// Get requestor's hospital ID
	id := ctx.Value("id").(string)
	if id == "" {
		return nil, ErrNilRequestorId
	}

	// Start transaction
	tx, err := s.db.Begin()
	if err != nil {
		return nil, err
	}

	// Check if there is an existing entry with a write lock
	row := tx.QueryRowContext(ctx, `SELECT hospital_id FROM patient_registrations WHERE patient_id = ? FOR UPDATE;`, request.Key)
	if err := row.Scan(&hospitalId); err != nil {
		if err != sql.ErrNoRows {
			_ = tx.Rollback()
			return nil, err
		}
		exists = false
	}

	// Cannot remove nonexistent key
	if !exists {
		// Rollback transaction
		_ = tx.Rollback()

		// Return failure response
		resp := RemoveResponse{Removed: false, ErrorType: RemoveError_REMOVE_KEY_ERROR}
		return &resp, nil
	}

	// Fail if an existing entry exists but the owner does not match
	if hospitalId != id {
		// Rollback transaction
		_ = tx.Rollback()

		// Return failure response
		resp := RemoveResponse{Removed: false, ErrorType: RemoveError_REMOVE_NOT_OWNER}
		return &resp, nil
	}

	// Delete row from database.
	res, err := tx.ExecContext(ctx, `DELETE FROM patient_registrations WHERE patient_id = ?;`, request.Key)
	if err != nil {
		_ = tx.Rollback()
		return nil, err
	}

	// Make sure that we deleted a row
	rowsAffected, err := res.RowsAffected()
	if err != nil {
		_ = tx.Rollback()
		return nil, err
	}
	if rowsAffected != 1 {
		_ = tx.Rollback()
		return nil, errors.New("no rows updated")
	}

	// Commit the transaction
	if err := tx.Commit(); err != nil {
		return nil, err
	}

	// Prepare response
	resp := RemoveResponse{Removed: true}
	return &resp, nil
}

func (s *Server) Transfer(ctx context.Context, request *TransferRequest) (*TransferResponse, error) {
	var hospitalId string
	exists := true

	// Get requestor's hospital ID
	id := ctx.Value("id").(string)
	if id == "" {
		return nil, ErrNilRequestorId
	}

	// Start transaction
	tx, err := s.db.Begin()
	if err != nil {
		return nil, err
	}

	// Check if there is an existing entry with a write lock
	row := tx.QueryRowContext(ctx, `SELECT hospital_id FROM patient_registrations WHERE patient_id = ? FOR UPDATE;`, request.Key)
	if err := row.Scan(&hospitalId); err != nil {
		if err != sql.ErrNoRows {
			_ = tx.Rollback()
			return nil, err
		}
		exists = false
	}

	// Cannot transfer nonexistent key
	if !exists {
		// Rollback transaction
		_ = tx.Rollback()

		// Return failure response
		resp := TransferResponse{Transferred: false, ErrorType: TransferError_TRANSFER_KEY_ERROR}
		return &resp, nil
	}

	// Fail if an existing entry exists but the owner does not match
	if hospitalId != id {
		// Rollback transaction
		_ = tx.Rollback()

		// Return failure response
		resp := TransferResponse{Transferred: false, ErrorType: TransferError_TRANSFER_NOT_OWNER}
		return &resp, nil
	}

	// Update owner in database.
	res, err := tx.ExecContext(ctx, `UPDATE patient_registrations SET hospital_id = ? WHERE patient_id = ?;`, request.NewOwner, request.Key)
	if err != nil {
		_ = tx.Rollback()
		return nil, err
	}

	// Make sure that we updated a row
	rowsAffected, err := res.RowsAffected()
	if err != nil {
		_ = tx.Rollback()
		return nil, err
	}
	if rowsAffected != 1 {
		_ = tx.Rollback()
		return nil, errors.New("no rows updated")
	}

	// Commit the transaction
	if err := tx.Commit(); err != nil {
		return nil, err
	}

	// Prepare response
	resp := TransferResponse{Transferred: true}
	return &resp, nil
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

	// Create a context value for passing
	valueCtx := context.WithValue(ctx, "id", r.Id)

	// Handle wrapped request and return wrapped response
	switch req := r.Request.(type) {
	case *WrappedRequest_Get:
		log.Printf("Received Get from %s: %s\n", r.Id, r.Request)
		if err := verify(req.Get); err != nil {
			return nil, err
		}
		resp, err := s.Get(valueCtx, req.Get)
		if err != nil {
			return nil, err
		}
		return &WrappedResponse{Response: &WrappedResponse_Get{Get: resp}}, nil

	case *WrappedRequest_Put:
		log.Printf("Received Put from %s: %s\n", r.Id, r.Request)
		if err := verify(req.Put); err != nil {
			return nil, err
		}
		resp, err := s.Put(valueCtx, req.Put)
		if err != nil {
			return nil, err
		}
		return &WrappedResponse{Response: &WrappedResponse_Put{Put: resp}}, nil

	case *WrappedRequest_Remove:
		log.Printf("Received Remove from %s: %s\n", r.Id, r.Request)
		if err := verify(req.Remove); err != nil {
			return nil, err
		}
		resp, err := s.Remove(valueCtx, req.Remove)
		if err != nil {
			return nil, err
		}
		return &WrappedResponse{Response: &WrappedResponse_Remove{Remove: resp}}, nil

	case *WrappedRequest_Transfer:
		log.Printf("Received Transfer from %s: %s\n", r.Id, r.Request)
		if err := verify(req.Transfer); err != nil {
			return nil, err
		}
		resp, err := s.Transfer(valueCtx, req.Transfer)
		if err != nil {
			return nil, err
		}
		return &WrappedResponse{Response: &WrappedResponse_Transfer{Transfer: resp}}, nil
	}

	return nil, errors.New("invalid request")
}

package golang_lib

import (
	"encoding/csv"
	"fmt"
	"os"
	"path"
	"path/filepath"
)

type PatientCard struct {
	Name       string
	PatientID  string
	uuid       string
	PublicKey  Unsigner
	PrivateKey Signer
}

func (c PatientCard) UUID() string {
	return c.uuid
}

func ParsePatientCards(directory string) ([]*PatientCard, error) {
	matches, err := filepath.Glob(path.Join(directory, "*.csv"))
	if err != nil {
		return nil, err
	}

	var cards []*PatientCard
	for _, filename := range matches {
		card, err := ParsePatientCard(filename)
		if err != nil {
			continue
		}
		cards = append(cards, card)
	}

	return cards, nil
}

func ParsePatientCard(filename string) (*PatientCard, error) {
	file, err := os.Open(filename)
	if err != nil {
		return nil, err
	}

	reader := csv.NewReader(file)

	// Skip header
	if _, err := reader.Read(); err != nil {
		return nil, err
	}

	// Read row
	row, err := reader.Read()
	if err != nil {
		return nil, err
	} else if len(row) != 5 {
		return nil, fmt.Errorf("expected 5 columns in row, got %d", len(row))
	}

	// Parse keys
	publicKey, err := ParsePublicKey([]byte(row[3]))
	if err != nil {
		return nil, fmt.Errorf("could not parse public key: %s", err)
	}
	privateKey, err := ParsePrivateKey([]byte(row[4]))
	if err != nil {
		return nil, fmt.Errorf("could not parse public key: %s", err)
	}

	card := PatientCard{
		Name:       row[0],
		PatientID:  row[1],
		uuid:       row[2],
		PublicKey:  publicKey,
		PrivateKey: privateKey,
	}

	return &card, nil
}

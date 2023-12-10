package parsers

import (
	"fmt"
	"strings"
	"time"
)

const IsoformatLayout = "2006-01-02T15:04:05.999"

type Time time.Time

func (t *Time) UnmarshalJSON(b []byte) error {
	timeStr := strings.Trim(string(b), "\"")

	resultTime, err := time.Parse(IsoformatLayout, timeStr)
	if err != nil {
		return fmt.Errorf("time unmarshal error: %w", err)
	}

	*t = Time(resultTime)
	return nil
}
func (t Time) String() string {
	return time.Time(t).Format(time.RFC3339)
}

type UserData struct {
	CreationDate Time   `json:"CreationDate"`
	UserName     string `json:"UserName"`
	MongoUserID  string `json:"MongoUserID"`
}

type UserDataSet map[string]UserData

type UserDataSetWithoutData map[string]struct {
	MongoUserID string `json:"MongoUserID"`
}

type UserDataMapFormated struct {
	UserID   string
	UserData UserData
}

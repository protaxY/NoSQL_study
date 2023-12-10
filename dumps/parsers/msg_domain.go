package parsers

type MsgDataSet struct {
	FromUser     string `json:"FromUser"`
	ToUser       string `json:"ToUser"`
	Message      string `json:"Message"`
	CreationDate Time   `json:"CreationDate"`
}

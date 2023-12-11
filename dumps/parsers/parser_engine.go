package parsers

import (
	"encoding/json"
	"fmt"
	"io"
	"os"

	"github.com/protaxY/NoSQL_study/dumps/my_logger"
)

func JsonParser[T any](pathToJSON string) (T, error) {
	var result T
	jsonFile, err := os.Open(pathToJSON)
	if err != nil {
		return result, fmt.Errorf("cant open file: %w", err)
	}
	defer jsonFile.Close()
	my_logger.LoggerVar.Infof("file %s has succesfully opened", pathToJSON)

	byteValue, err := io.ReadAll(jsonFile)
	if err != nil {
		return result, fmt.Errorf("cant read file: %w", err)
	}

	err = json.Unmarshal([]byte(byteValue), &result)
	if err != nil {
		return result, fmt.Errorf("cant unmarshal json file: %w", err)
	}
	my_logger.LoggerVar.Infof("file %s has succesfully unmarshaled", pathToJSON)

	return result, nil
}

func JsonSaver[T any](pathToFile string, result T) error {
	my_logger.LoggerVar.Info("Users are ready. Saving progress into file")
	file, err := json.MarshalIndent(result, "", " ")
	if err != nil {
		return fmt.Errorf("cannot marshal result file: %w", err)
	}

	err = os.WriteFile(pathToFile, file, os.ModeAppend)
	if err != nil {
		return fmt.Errorf("cannot save result file: %w", err)
	}

	return nil
}

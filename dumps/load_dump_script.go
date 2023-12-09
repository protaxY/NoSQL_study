package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"os/signal"
	"strings"
	"sync"
	"syscall"
	"time"

	"github.com/schollz/progressbar/v3"
	"github.com/withmandala/go-log"
)

const (
	isoformatLayout = "2006-01-02T15:04:05.999"
	workersCount    = 300
)

type myLogger struct {
	logIntoFile   *log.Logger
	logIntoConsol *log.Logger
}

func (l *myLogger) Error(v ...interface{}) {
	l.logIntoConsol.Error(v...)
	l.logIntoFile.Error(v...)
}
func (l *myLogger) Errorf(format string, v ...interface{}) {
	l.logIntoConsol.Errorf(format, v...)
	l.logIntoFile.Errorf(format, v...)
}
func (l *myLogger) Info(v ...interface{}) {
	l.logIntoConsol.Info(v...)
	l.logIntoFile.Info(v...)
}
func (l *myLogger) Infof(format string, v ...interface{}) {
	l.logIntoConsol.Infof(format, v...)
	l.logIntoFile.Infof(format, v...)
}

var loggerVar myLogger

func init() {
	f, err := os.Create("app.log")
	if err != nil {
		fmt.Println("cant open log file")
		os.Exit(1)
	}
	loggerVar = myLogger{
		logIntoFile:   log.New(f).WithoutColor(),
		logIntoConsol: log.New(os.Stderr).WithColor(),
	}

}

type Time time.Time

func (t *Time) UnmarshalJSON(b []byte) error {
	timeStr := strings.Trim(string(b), "\"")

	resultTime, err := time.Parse(isoformatLayout, timeStr)
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

func jsonParser[T any](pathToJSON string) (T, error) {
	var result T
	jsonFile, err := os.Open(pathToJSON)
	if err != nil {
		return result, fmt.Errorf("cant open file: %w", err)
	}
	defer jsonFile.Close()
	loggerVar.Infof("file %s has succesfully opened", pathToJSON)

	byteValue, err := io.ReadAll(jsonFile)
	if err != nil {
		return result, fmt.Errorf("cant read file: %w", err)
	}

	err = json.Unmarshal([]byte(byteValue), &result)
	if err != nil {
		return result, fmt.Errorf("cant unmarshal json file: %w", err)
	}
	loggerVar.Infof("file %s has succesfully unmarshaled", pathToJSON)

	return result, nil
}

type UserDataMapFormated struct {
	UserID   string
	UserData UserData
}

func createUserReq(host string, readUserDataChan <-chan UserDataMapFormated, writeUseraDataChan chan UserDataMapFormated, workerCount int) {
	method := "POST"
	client := &http.Client{}
	loggerVar.Infof("craeting %d worker", workerCount)

	for userData := range readUserDataChan {
		params := url.Values{}
		params.Add("username", userData.UserData.UserName)
		params.Add("name", userData.UserData.UserName)
		params.Add("timestamp", time.Time(userData.UserData.CreationDate).Format(isoformatLayout))
		url := fmt.Sprintf("%s?%s", host, params.Encode())

		req, err := http.NewRequest(method, url, nil)
		if err != nil {
			loggerVar.Errorf("User cant be added due request error [userName=%s, userID=%s]: %s", userData.UserData.UserName, userData.UserID, err.Error())
			continue
		}

		res, err := client.Do(req)
		if err != nil {
			loggerVar.Errorf("User cant be added due request DO error [userName=%s, userID=%s]: %s", userData.UserData.UserName, userData.UserID, err.Error())
			continue
		}

		if res.StatusCode != http.StatusOK {
			body, err := io.ReadAll(res.Body)
			if err != nil {
				loggerVar.Errorf("cannot ready body while getting status code %d [userName=%s, userID=%s]: %s", res.StatusCode, userData.UserData.UserName, userData.UserID, err.Error())
				res.Body.Close()
				continue
			}
			loggerVar.Errorf("status code %d [userName=%s, userID=%s]\nBody: %s", res.StatusCode, userData.UserData.UserName, userData.UserID, body)
			res.Body.Close()
			continue
		}

		body, err := io.ReadAll(res.Body)
		if err != nil {
			loggerVar.Errorf("cannot ready body [userName=%s, userID=%s]: %s", userData.UserData.UserName, userData.UserID, err.Error())
			res.Body.Close()
			continue
		}

		// prepare to send to channel
		userData.UserData.MongoUserID = string(body)
		res.Body.Close()

		writeUseraDataChan <- userData
	}

	loggerVar.Infof("readUserDataChan has been closed. Turning off worker %d channels...", workerCount)
}

func workerReader(wg *sync.WaitGroup, progressbar *progressbar.ProgressBar, writeUseraDataChan <-chan UserDataMapFormated) UserDataSet {
	result := make(UserDataSet)
	defer wg.Done()

	for userData := range writeUseraDataChan {
		result[userData.UserID] = userData.UserData
		progressbar.Add(1)

	}
	loggerVar.Info("writeUseraDataChan has been closed. Turning off worderReader...")
	return result
}

func main() {
	ctx, cancel := context.WithCancel(context.Background())

	users, err := jsonParser[UserDataSet]("./users_data_set.json")
	if err != nil {
		loggerVar.Error(err)
	}

	// start workers
	readUserDataChan := make(chan UserDataMapFormated, workersCount)
	writeUseraDataChan := make(chan UserDataMapFormated)

	for i := 0; i < workersCount; i++ {
		go createUserReq("http://localhost/messenger/users", readUserDataChan, writeUseraDataChan, i)
	}

	var (
		wg            sync.WaitGroup
		result        UserDataSet
		bar           = progressbar.Default(int64(len(users)), "status")
		channelClosed bool
	)
	wg.Add(1)
	go func() {
		result = workerReader(&wg, bar, writeUseraDataChan)
	}()

	interaptKeyChan := make(chan os.Signal, 1)
	signal.Notify(interaptKeyChan, os.Interrupt, syscall.SIGTERM)
	go func() {
		<-interaptKeyChan
		cancel()
		loggerVar.Info("Key interrapt has been triggered")
	}()

L:
	for userID, userData := range users {
		select {
		case <-ctx.Done():
			loggerVar.Info("Canceling intration")
			close(readUserDataChan)
			loggerVar.Info("waiting for 5 seconds to complite tasks...")
			time.Sleep(5 * time.Second)
			close(writeUseraDataChan)
			channelClosed = true
			break L
		default:
			userDataToSend := UserDataMapFormated{
				UserID:   userID,
				UserData: userData,
			}

			readUserDataChan <- userDataToSend
		}
	}

	if !channelClosed {
		close(readUserDataChan) // возможна потеря данных
		loggerVar.Info("waiting for 40 seconds to complite tasks...")
		time.Sleep(40 * time.Second)
		close(writeUseraDataChan)
	}

	wg.Wait()
	loggerVar.Info("Users are ready. Saving progress into file")
	file, err := json.MarshalIndent(result, "", " ")
	if err != nil {
		loggerVar.Errorf("Cannot marshal result file: %s", err.Error())
		return
	}

	err = os.WriteFile("users_result.json", file, os.ModeAppend)
	if err != nil {
		loggerVar.Errorf("Cannot save result file: %s", err.Error())
	}
}
